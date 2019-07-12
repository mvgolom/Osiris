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
from Repository import Extractions as ext
try:
    from CrawlerLibs import follow, cyclopslair
except ImportError as error:
    raise ImportError(error)

projectUserAssociation = {"COMMITTER":"committers","MEMBER":"members","OWNER":"owner","CONTRIBUTOR":"contributors","COLLABORATOR":"collaborators"}

client = MongoClient('localhost', 27017)

def statusInProject(nameOpt=None):
    client = MongoClient('localhost', 27017)
    db = client["global_metrics"]
    db2 = client["global_status"]
    db3 = client["global_metrics_final"]
    if nameOpt != None:
        allMetrics = list(db.projectMetrics.find({"projectName":nameOpt}))
    else:
        allMetrics = list(db.projectMetrics.find({}))

    auxstate = list(db2.global_status_names.find({}))
    auxStatusGlobal = []
    for projectState in auxstate:
         auxStatusGlobal.append(projectState.get("login"))

    statusGlobal = {}

    print(len(allMetrics))
    print(len(auxStatusGlobal))
    
    for status in auxstate:
        loginStatus = status.get("login")
        qtProject = status.get("qtProject")
        statusGlobal[loginStatus] = qtProject

    
    for repoMetrics in allMetrics:
        projectName = repoMetrics.get("projectName")

        print(projectName)

        committers = repoMetrics.get("committers")
        auxCommitters = []
        if committers != []:
            for committer in committers:
                committerlogin = committer.get("login")
                contentValueInProject = committer.get("contentValueInProject") 
                longTimeInteraction = committer.get("longTimeInteraction")
                if committerlogin in auxStatusGlobal:
                    value = statusGlobal[committerlogin]
                    committer["statusInProject"] = value
                try:
                    contentValueInProject = contentValueInProject.get("$numberDouble")
                    longTimeInteraction = longTimeInteraction.get("$numberDouble")
                except:
                    continue
                
                committer["contentValueInProject"] = contentValueInProject
                committer["longTimeInteraction"] = longTimeInteraction
                del committer["_id"]

                auxCommitters.append(committer)

        
        members = repoMetrics.get("members")
        auxMembers = []
        if members != []:
            for member in members:
                memberlogin = member.get("login")
                contentValueInProject = member.get("contentValueInProject") 
                longTimeInteraction = member.get("longTimeInteraction")
                if memberlogin in auxStatusGlobal:
                    value = statusGlobal[memberlogin]
                    member["statusInProject"] = value
                try:
                    contentValueInProject = contentValueInProject.get("$numberDouble")
                    longTimeInteraction = longTimeInteraction.get("$numberDouble")
                except:
                    continue
                
                member["contentValueInProject"] = contentValueInProject
                member["longTimeInteraction"] = longTimeInteraction
                del member["_id"]

                auxMembers.append(member)
        
        collaborators = repoMetrics.get("collaborators")
        auxCollaborators = []
        if collaborators != []:
            for collaborator in collaborators:
                collaboratorlogin = collaborator.get("login")
                contentValueInProject = collaborator.get("contentValueInProject") 
                longTimeInteraction = collaborator.get("longTimeInteraction")

                if collaboratorlogin in auxStatusGlobal:
                    value = statusGlobal[collaboratorlogin]
                    collaborator["statusInProject"] = value
                try:
                    contentValueInProject = contentValueInProject.get("$numberDouble")
                    longTimeInteraction = longTimeInteraction.get("$numberDouble")
                except:
                    continue
                
                collaborator["contentValueInProject"] = contentValueInProject
                collaborator["longTimeInteraction"] = longTimeInteraction
                del collaborator["_id"]

                auxCollaborators.append(collaborator)
        

        contributors = repoMetrics.get("contributors")
        auxContributors = []
        if contributors != []:
            for contributor in contributors:
                contributorlogin = contributor.get("login")
                contentValueInProject = contributor.get("contentValueInProject") 
                longTimeInteraction = contributor.get("longTimeInteraction") 
                if contributorlogin in auxStatusGlobal:
                    value = statusGlobal[contributorlogin]
                    contributor["statusInProject"] = value
                try:
                    contentValueInProject = contentValueInProject.get("$numberDouble")
                    longTimeInteraction = longTimeInteraction.get("$numberDouble")
                except:
                    continue
                
                contributor["contentValueInProject"] = contentValueInProject
                contributor["longTimeInteraction"] = longTimeInteraction
                del contributor["_id"]

                auxContributors.append(contributor)
        
        owner = repoMetrics.get("owner")
        auxOwner = {}
        if owner != None:
            ownerlogin = owner.get("login") 
            contentValueInProject = owner.get("contentValueInProject") 
            longTimeInteraction = owner.get("longTimeInteraction") 

            if ownerlogin in auxStatusGlobal:
                value = statusGlobal[ownerlogin]
                owner["statusInProject"] = value
            try:
                contentValueInProject = contentValueInProject.get("$numberDouble")
                longTimeInteraction = longTimeInteraction.get("$numberDouble")
            except:
                continue
            
            owner["contentValueInProject"] = contentValueInProject
            owner["longTimeInteraction"] = longTimeInteraction
            del owner["_id"]

            auxOwner = owner

        else:
            auxOwner = None

        newProject = {
            "projectName":projectName,
            "members":auxMembers,
            "committers":auxCommitters,
            "contributors":auxContributors,
            "collaborators":auxCollaborators,
            "owner":auxOwner
        }

        try:
            db3.projectMetricsFinal.insert(newProject)
            print(newProject.get("projectName"))
        except Pymongo.errors.DuplicateKeyError:
            continue

def participationWComments(owner,repo,authen):
    print ("participation With Comments .......")
    global client
    dbname = (repo+"_metrics")
    db = client[repo]
    db2 = client[dbname]
    global projectUserAssociation

    userComments = {}
    userCommentsArray = []

    allUsers = ext.getlistUsers(owner,repo)

    allCommentsUser = list(db.issuesComments.find({}))
    for usercomment in allCommentsUser:
        occurrence = usercomment.get("participants")
        if occurrence != None:
            occurrenceKeys = list(occurrence.keys())
            for userlogin in occurrenceKeys:
                if userlogin in userCommentsArray:
                    value = occurrence.get(userlogin)
                    userComments[userlogin] = userComments[userlogin]+int(value)
                else:
                    userComments[userlogin] = int(occurrence.get(userlogin))
                    userCommentsArray.append(userlogin)
    
    for user in allUsers:
        userlogin = user.get("login")
        if userlogin in userCommentsArray:
            try:
                association = user.get("association")
                userDB = projectUserAssociation.get(association)
                db2[userDB].update({"login":user.get("login")},{"$set": {"participationWComments": userComments.get(userlogin)}})
            except Pymongo.errors.OperationFailure as e:
                print(e)
        else:
            try:
                print((user.get("login")))
                collect = user.get("association")
                association = user.get("association")
                userDB = projectUserAssociation.get(association)
                db2[userDB].update({"login":user.get("login")},{"$set": {"participationWComments": 0}})
            except Pymongo.errors.OperationFailure as e:
                print(e)

def longTimeInteractionWproject(owner,repo,authen):
    print ("long Time Interaction With Project .......")
    global client
    dbname = (repo+"_metrics")
    db = client[repo]
    db2 = client[dbname]
    allUsers = ext.getlistUsers(owner,repo)
    global projectUserAssociation
    for user in allUsers:
        association = user.get("association")
        userDB = projectUserAssociation.get(association)
        userLogin = user.get("login")
        userAux = db2[userDB].find_one({"login":userLogin})
        if userAux != None:
            qtComments = userAux.get("participationWComments")
            qtCommits = len(list(db.commits.find({"author.login":userLogin})))
            actions = qtComments+qtCommits
            timeInRepo = daysInProject(userLogin,db)
            if(timeInRepo > 0):
                longTimeInteraction = float(actions)/float(timeInRepo)
            else:
                longTimeInteraction = 0
            db2[userDB].update({"login":userLogin},{"$set": {"longTimeInteraction": longTimeInteraction}})

def contentValueInProject(owner,repo,authen):
    print ("content Value In Project .......")
    global client
    dbname = (repo+"_metrics")
    db = client[repo]
    db2 = client[dbname]

    
    userCommits = {}
    userCommitsArray = []

    allUsers = ext.getlistUsers(owner,repo)

    for user in allUsers:
        allcommitsInfo = list(db.commitsInfo.find({"author":user.get("login")}))
        userlogin = user.get("login")
        for commitsInfo in allcommitsInfo:
            value = float(commitsInfo.get("contentValue"))
            
            if userlogin in userCommitsArray:
                userCommits[userlogin] = userCommits[userlogin]+value
            else:
                userCommits[userlogin] = float(value)
                userCommitsArray.append(userlogin)
            
        if userlogin in userCommitsArray:
            contentValueInProject = userCommits.get(userlogin)
            try:
                association = user.get("association")
                userDB = projectUserAssociation.get(association)
                db2[userDB].update({"login":user.get("login")},{"$set": {"contentValueInProject": contentValueInProject}})
            except Pymongo.errors.OperationFailure as e:
                print(e)
        else:
            try:
                print((user.get("login")))
                collect = user.get("association")
                association = user.get("association")
                userDB = projectUserAssociation.get(association)
                db2[userDB].update({"login":user.get("login")},{"$set": {"contentValueInProject": 0}})    
            except Pymongo.errors.OperationFailure as e:
                print(e)

def ParticipationWcode(owner,repo,authen):
    print ("participation With Comments .......")
    global client
    dbname = (repo+"_metrics")
    db = client[repo]
    db2 = client[dbname]
    allUsers = ext.getlistUsers(owner,repo)
    for user in allUsers:
        allprOpen = list(db.pullrequests.find({"author.login":user.get("login")}))
        qtprOpen = len(allprOpen)
        allprClosed = list(db.prInfo.find({"mergedby":user.get("login")}))
        qtprClosed = len(allprClosed)
        ParticipationWcode = int(qtprClosed+qtprOpen)
        if ParticipationWcode > 0:
            try:
                association = user.get("association")
                userDB = projectUserAssociation.get(association)
                db2[userDB].update({"login":user.get("login")},{"$set": {"participationWcode": ParticipationWcode}})
            except Pymongo.errors.OperationFailure as e:
                print(e)
        else:
            try:
                print((user.get("login")))
                association = user.get("association")
                userDB = projectUserAssociation.get(association)
                db2[userDB].update({"login":user.get("login")},{"$set": {"participationWcode": 0}})
            except Pymongo.errors.OperationFailure as e:
                print(e)

def sourceOfLearning(owner,repo,authen):
    print("sourceOfLearning .....")
    global client
    dbname = (repo+"_metrics")
    db = client[repo]
    db2 = client[dbname]
    userMentions = {}
    userMentionsArray = []
    
    allUsers = ext.getlistUsers(owner,repo)
    
    for user in allUsers:
        allMentionUser = list(db.issuesComments.find({"mentions":user.get("login")}))
        if len(allMentionUser) > 0:
            userlogin = user.get("login")
            for usermention in allMentionUser:
                mentionsN = usermention.get("mentions")
                occurrence = Counter(mentionsN)
                if userlogin in userMentionsArray:
                    value = occurrence.get(userlogin)
                    userMentions[userlogin] = userMentions[userlogin]+int(value)
                else:
                    if(occurrence.get(userlogin) != None):
                        userMentions[userlogin] = int(occurrence.get(userlogin))
                        userMentionsArray.append(userlogin)
            if userlogin in userMentionsArray:
                try:
                    association = user.get("association")
                    userDB = projectUserAssociation.get(association)
                    db2[userDB].update({"login":user.get("login")},{"$set": {"sourceOfLearning": userMentions.get(userlogin)}})
                except Pymongo.errors.OperationFailure as e:
                    print(e)
        else:
            try:
                print((user.get("login")))
                association = user.get("association")
                userDB = projectUserAssociation.get(association)
                db2[userDB].update({"login":user.get("login")},{"$set": {"sourceOfLearning": 0}})
            except Pymongo.errors.OperationFailure as e:
                print(e)

def status(owner,repo,authen):
    global client
    dbname = (repo+"_metrics")
    db2 = client[dbname]
    flw = follow.followers(authen)
    userList = ext.getlistUsers(owner,repo)
    allUsers = list(userList)
    followers = flw.followersList(allUsers)
    for user in allUsers:
        print((user["login"]))
        userlogin = user["login"]
        if(userlogin != None):
            followersqtd = followers[userlogin]
        else:
            followersqtd = 0
        try:
            association = user.get("association")
            userDB = projectUserAssociation.get(association)
            db2[userDB].update({"login":user.get("login")},{"$set": {"status": followersqtd}})
        except Pymongo.errors.OperationFailure as e:
            print(e)
            continue

def daysInProject(user,dbclient):
    commitlist = list(dbclient.commits.find({'author.login':user}).sort('commit.author.date', 1).limit(1))
    issuelist = list(dbclient.issues.find({'user.login':user}).sort('created_at', 1).limit(1))
    firstcommit = 0
    firstIssue = 0
    datenow = str(datetime.datetime.date(datetime.datetime.now()))
    d2 = datetime.datetime.strptime(datenow, "%Y-%m-%d")
    if len(commitlist) > 0:
        commit = commitlist[0]
        date1 = commit.get("commit").get("author").get("date")
        date1f = str(date1.split("T")[0])
        d1 = datetime.datetime.strptime(date1f, "%Y-%m-%d")
        firstcommit = abs((d2 - d1).days)
    
    if len(issuelist) > 0:
        issue = issuelist[0]
        date1 = issue.get("created_at")
        date1f = date1.split("T")[0]
        d1 = datetime.datetime.strptime(date1f, "%Y-%m-%d")
        firstIssue = abs((d2 - d1).days)
    
    if(firstcommit >= firstIssue):
        return firstcommit
    else:
        return firstIssue


#https://developer.github.com/v3/users/followers/#check-if-one-user-follows-another

def closenessOwner(owner,repo,authen):
    global client
    print("closeness in project .....")
    dbname = (repo+"_metrics")
    db = client[dbname]
    ownerList = db.owner.find_one({})
    members = list(db.members.find({},{"_id":0}))
    users = ext.getlistUsers(owner,repo)
    allUsers = list(users)
    memberLen = len(members)
    ownerLen = 0
    flw = follow.followers(authen)
    if ownerList != None:
        ownerLen = 1
    
    if (ownerLen > 0) and (memberLen > 0):
        followings = flw.followingsList(ownerList.get("login"))
        if followings != 0:
            for user in allUsers:
                if user in followings:
                    db.owner.update({"login":ownerList.get("login")},{"$push":{"closeness":user}})
        else:
            db.owner.update({"login":ownerList.get("login")},{"$push":{"closeness":0}})

        memberList = list(members)
        for member in memberList:
            results = follow.followingsList(member.get("login"))
            if results != 0:
                followings = list(results)
                flag = False
                for user in allUsers:
                    if user in followings:
                        print((("{}:{}").format(member.get("login"),user.get("login"))))
                        flag = True
                        db.members.update({"login":member.get("login")},{"$push":{"closeness":user}})
                if(flag == False):
                    db.members.update({"login":member.get("login")},{"$push":{"closeness":0}})
            else:
                print((("{}:{}").format(member.get("login"),0)))
                db.members.update({"login":member.get("login")},{"$push":{"closeness":0}})

    elif(ownerLen > 0) and (memberLen == 0):
        followings = flw.followingsList(ownerList.get("login"))
        if followings != 0:
            for user in allUsers:
                if user in followings:
                    db.owner.update({"login":ownerList.get("login")},{"$push":{"closeness":user}})
        else:
            db.owner.update({"login":ownerList.get("login")},{"$push":{"closeness":0}})
    
    elif(ownerLen == 0) and (memberLen > 0):
        memberList = list(members)
        for member in memberList:
            results = flw.followingsList(member.get("login"))
            if results != 0:
                followings = list(results)
                flag = False
                for user in allUsers:
                    if user in followings:
                        print((("{}:{}").format(member.get("login"),user.get("login"))))
                        flag = True
                        db.members.update({"login":member.get("login")},{"$push":{"closeness":user}})
                if(flag == False):
                    db.members.update({"login":member.get("login")},{"$push":{"closeness":0}})
            else:
                print((("{}:{}").format(member.get("login"),0)))
                db.members.update({"login":member.get("login")},{"$push":{"closeness":0}})
