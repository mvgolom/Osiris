import re
import sys
import json
import time
import datetime
import requests
import unicodedata
import pathos.pools as mp
import pymongo as Pymongo
import multiprocessing as mtp
from itertools import chain
from collections import Counter
from pymongo import MongoClient
from joblib import Parallel, delayed
try:
    from Octopus import crawler, search, repository
except ImportError as error:
    raise ImportError(error)
try:
    from CrawlerLibs import follow, cyclopslair, cyclops
except ImportError as error:
    raise ImportError(error)

projectUserAssociation = {"COMMITTER":"committers","MEMBER":"members","OWNER":"owner","CONTRIBUTOR":"contributors","COLLABORATOR":"collaborators"}
client = MongoClient('localhost', 27017)


def getInfo(projetoName,authen):
    client = MongoClient('localhost', 27017)
    inicio = time.time()
    arg = projetoName.split("/")
    namerepo = ""
    if "." in arg[1]:
        namerepo = arg[1].replace(".","")
    else:
        namerepo = arg[1]
    
    if len(namerepo) >= 64:
        namerepo = namerepo[0:62]

    db = client[namerepo]

    stateClose = "closed"
    stateOpen = "open"

    crawlerP = crawler.Crawler(authen)

    repo_object = repository.Repository(arg[0], arg[1], crawlerP)
    
    commits = repo_object.commits()
    for item in commits:
        try:
            db.commits.insert(item)
        except TypeError as e:
            print('I got a TypeError - reason "%s"' % str(e))
            pass
    
    pullRequestsOpen = repo_object.pull_requests(stateOpen)
    for item in pullRequestsOpen:
        try:
            db.pullrequests.insert(item)
        except TypeError as e:
            print('I got a TypeError - reason "%s"' % str(e))
            pass

    pullRequestsClosed = repo_object.pull_requests(stateClose)
    for item in pullRequestsClosed:
        try:
            db.pullrequests.insert(item)
        except TypeError as e:
            print('I got a TypeError - reason "%s"' % str(e))
            pass

    contributors = repo_object.contributors()
    for item in contributors:
        try:
            db.contributors.insert(item)
        except TypeError as e:
            print('I got a TypeError - reason "%s"' % str(e))
            pass

    issuesOpen = repo_object.issues(stateOpen)
    for item in issuesOpen:
        try:
            db.issues.insert(item)
        except TypeError as e:
            print('I got a TypeError - reason "%s"' % str(e))
            pass

    issuesClose = repo_object.issues(stateClose)
    for item in issuesClose:
        try:
            db.issues.insert(item)
        except TypeError as e:
            print('I got a TypeError - reason "%s"' % str(e))
            pass
            


def getLoginAssociation(userObj,owner):
    try:
        login = userObj.get("user").get("user").get("login")
        association = userObj.get("user").get("author_association")

        if association == "NONE":
            association = "COMMITTER"
        elif login == owner:
            association = "OWNER"
        aux ={
            "login":login,
            "association":association
        }
        return aux
    except KeyError as e:
        print(('I got a KeyError - reason "{}"').format(str(e)))
    except IndexError as e:
        print('I got an IndexError - reason "%s"' % str(e))


def getAllContributors(owner,repo):
    client = MongoClient('localhost', 27017)
    print("Get all Users .......")
    dbname = (repo+"_metrics")
    db = client[repo]
    db2 = client[dbname]
    cursor = list(db.contributors.find({},{"_id":0,"login":1}))
    
    userType = ["userAssociates","owner","members","contributors","collaborators","committers"]
    index_name = "uniqueLogin"
    for types in userType:
        my_collection = db2[types]
        my_collection.create_index([('login',1)], name=index_name, unique=True)
    
    
    for contributor in cursor:
        data = contributor
        try:
            db2.committers.insert({"login":data.get("login"),"association":"COMMITTER"})
        except Pymongo.errors.DuplicateKeyError:
            continue
    
    final = db.pullrequests.aggregate([
    {"$sort": { "user.login": 1}}, 
    {"$group":{ 
        "_id": "$user.login", 
        "user": { "$last": "$$ROOT" } 
    }
    } 
    ],allowDiskUse=True)
    
    final = list(final)
    print("Extract Associations .....")
    results = Parallel(n_jobs=mtp.cpu_count())(delayed(getLoginAssociation)(x,owner) for x in final)
    # print results
    for user in results:
        login = str(user.get("login"))
        associ = user.get("association")
        try:
            association = user.get("association")
            login = login.strip()
            owner = owner.strip()
            # print login+"-->"+owner
            if(login == owner):
                association = "OWNER"
            userDB = projectUserAssociation.get(association)
            db2[userDB].insert({"login":login,"association":associ})
            db2.userAssociates.insert({"login":login,"association":associ})
        except Pymongo.errors.DuplicateKeyError:
            continue

        userType = ["owner","members","contributors","collaborators"]
        for types in userType:
            aux = db2[types].find({})
            for x in aux:
                try:
                    db2.committers.delete_one({"login":x.get("login")})
                except Pymongo.errors.OperationFailure as e:
                    print(e)
                    continue
        

def getAllComments(owner,repo,authen):
    client = MongoClient('localhost', 27017)
    db = client[repo]

    #get issues with range less than 100 elements
    allIssuesComments = list(db.issues.find({"comments": {"$exists":True,"$lt":101,"$gt":0}}))
    print(len(allIssuesComments))
    resultList = cyclopslair.getIssuesCommentsList(allIssuesComments,owner,repo,authen)
    for issue in allIssuesComments:
        issue["number"]
        try:
            db.issuesComments.insert({"number":issue.get("number"),"qtComments":issue.get("comments"),"comments":resultList.get(issue.get("number"))})
        except KeyError as e:
            print('I got a KeyError - reason "%s"' % str(e))
        except IndexError as e:
            db.issuesComments.insert({"number":issue.get("number"),"qtComments":0,"comments":0})
            print('I got an IndexError - reason "%s"' % str(e))
    
    #get issues with range great than 100 elements
    allIssuesComments = list(db.issues.find({"comments": {"$exists":True,"$gte":101}}))
    print(len(allIssuesComments))
    for issue in allIssuesComments:
        resultList = cyclopslair.getIssuesCommentsOne(issue.get("comments_url"),owner,repo,authen)
        db.issuesComments.insert({"number":issue.get("number"),"qtComments":issue.get("comments"),"comments":resultList})
    
    #get issues with 0 comments
    allIssuesComments = list(db.issues.find({"comments": {"$exists":True,"$eq":0}}))
    print(len(allIssuesComments))
    for issue in allIssuesComments:
        db.issuesComments.insert({"number":issue.get("number"),"qtComments":0,"comments":0})

def getMentions(issueComments):
    print(("issues: {}").format(issueComments.get("number")))
    pattern = re.compile(r"(\@\w*)")
    mentions = []
    participants = {}
    arrayParticipants = []
    # print issueComments
    # print issueComments.get("number")
    comments = issueComments.get("comments")
    if comments != None:
        for comment in comments:
            aux = pattern.findall(comment.get("body"))
            if aux != []:
                mentions.append(aux)
            else:
                mentions.append(aux)

            try:
                # print comment.get("user").get("login")
                if comment.get("user").get("login") in arrayParticipants:
                    aux = comment.get("user").get("login")
                    participants[aux] = participants[aux]+1
                else:
                    participants[comment["user"]["login"]] = 1
                    arrayParticipants.append(comment["user"]["login"])
            except KeyError as e:
                print('I got a KeyError - reason "%s"' % str(e))
            except IndexError as e:
                print('I got an IndexError - reason "%s"' % str(e))

        itemsMentions = list(chain.from_iterable(mentions[i] for i in range(len(mentions))))
        itemsAux = [i.replace('@', '') for i in itemsMentions]
        items = []
        for k in itemsAux:
            if k != "":
                items.append(k)
        
        item = {
            "number":issueComments.get("number"),
            "participants":participants,
            "mentions":items
        }
        return item

def getIssuesMentions(owner,repo,authen):
    print("get Issues Mentions ......")
    client = MongoClient('localhost', 27017)
    db = client[repo]
    print(db)
    allIssueComments = list(db.issuesComments.find({"qtComments": {"$exists":True,"$gt":0}}))
    print(len(allIssueComments))
    itemsComments = Parallel(n_jobs=mtp.cpu_count())(delayed(getMentions)(x)for x in allIssueComments)
    print(len(itemsComments))
    return itemsComments

def getAllCommentsTypes(owner,repo,authen):
    client = MongoClient('localhost', 27017)
    dbname = (repo+"_metrics")
    db = client[repo]
    db2 = client[dbname]

    #All Commenters get here-------
    getAllComments(owner,repo,authen)
    #------------------------------
    
    commentF = getIssuesMentions(owner,repo,authen)

    # print commentF
    for commentBox in commentF:
        if commentBox != None:
            try:
                if(commentBox["mentions"] != []):
                    db.issuesComments.update({"number":commentBox.get("number")},{"$set": {"mentions":commentBox.get("mentions")}})
                else:
                    db.issuesComments.update({"number":commentBox.get("number")},{"$set": {"mentions":0}})

                db.issuesComments.update({"number":commentBox.get("number")},{"$set": {"participants":commentBox.get("participants")}})
            except Pymongo.errors.OperationFailure as e:
                print(e)

def getlistUsers(owner,repo):
    client = MongoClient('localhost', 27017)
    dbname = (repo+"_metrics")
    db = client[repo]
    db2 = client[dbname]

    allUsers = []
    aux = []
    
    allcommitters = list(db2.committers.find({}))
    aux.append(allcommitters)
    allowner = list(db2.owner.find({}))
    aux.append(allowner)
    allcontributors = list(db2.contributors.find({}))
    aux.append(allcontributors)
    allmembers = list(db2.members.find({}))
    aux.append(allmembers)
    allcollaborators = list(db2.collaborators.find({}))
    aux.append(allcollaborators)
    allUsers = list(chain.from_iterable(aux[i] for i in range(len(aux))))
    return allUsers



def codeGetterInfo(owner,repo,authen):
    client = MongoClient('localhost', 27017)
    dbname = (repo+"_metrics")
    db = client[repo]
    db2 = client[dbname]
    allCommits = list(db.commits.find({}))
    print(len(allCommits))
    resultListCommit = cyclopslair.getCommitInfoList(allCommits,owner,repo,authen)
    print(len(resultListCommit))
    for commit in resultListCommit:
        db.commitsInfo.insert({"sha":commit.get("sha"),"author":commit.get("author"),"committer":commit.get("committer"),\
        "filequantity":commit.get("filequantity"),"deletions":commit.get("deletions"),"additions":commit.get("additions"),\
        "totalModified":commit.get("totalModified"),"contentValue":commit.get("contentValue")})
    
    allIssue = list(db.pullrequests.find({}))
    print(len(allIssue))
    resultListIssues = cyclopslair.getPRInfoList(allIssue,owner,repo,authen)
    for pr in resultListIssues:
        db.prInfo.insert({"number":pr.get("number"),"author":pr.get("author"),"merged":pr.get("merged"),\
        "mergedby":pr.get("mergedby"),"filequantity":pr.get("filequantity"),"deletions":pr.get("deletions"),"additions":pr.get("additions"),\
        "prState":pr.get("prState"),"mergedInCommit":pr.get("mergedInCommit"),"created_at":pr.get("created_at"),"merged_at":pr.get("merged_at"),\
        "totalModified":pr.get("totalModified"),"contentValue":pr.get("contentValue")})

def ownerSearch(ownerRepo,repo,name,authen):
    client = MongoClient('localhost', 27017)
    cyc = cyclops.Cyclops(authen)
    global projectUserAssociation
    urlRepo = ("https://api.github.com/repos/{}".format(name))
    jsonReturn = cyc.requestOne(urlRepo,raw=True)
    ownerName = ("{}:{}".format(name,jsonReturn.get("owner").get("login")))

    dbname = (repo+"_metrics")
    db = client[dbname]
    members = list(db.members.find({}))
    ownerList = list(db.owner.find({}))
    alluser = getlistUsers(ownerRepo,repo)
    if(len(members) == 0):
        if(len(ownerList) == 0):
            for user in alluser:
                login = user.get("login")
                association = user.get("association")
                dbName = projectUserAssociation[association]
                if login == ownerRepo:
                    auxUser = db[dbName].find_one({"login":login})
                    db[dbName].delete_one({"login":login})
                    auxUser["association"] = "OWNER"
                    db.owner.insert_one(auxUser)
