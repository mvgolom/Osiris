#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#Author: Marcos Golom
#Contact: viniciusgolom@gmail.com
import urllib.request, urllib.error, urllib.parse
import requests
import time
import datetime
import json
import urllib.parse
import joblib
from . import cyclops
import multiprocessing as mtp
from pymongo import MongoClient
from itertools import chain
from itertools import cycle
from joblib import Parallel, delayed


def byteify(self,input):
    if isinstance(input, dict):
        return {self.byteify(key): self.byteify(value)
                for key, value in input.items()}
    elif isinstance(input, list):
        return [self.byteify(element) for element in input]
    elif isinstance(input, str):
        return input.encode('utf-8')
    else:
        return input

def getcommitsInfos(commit):
    if commit != None:
        commitInfo = commit.get("commitInfo")
        sha = commit.get("sha")

        author = ""
        authorAux = commitInfo.get("author")
        if authorAux != None:
            author = authorAux.get("login")
        else:
            author = authorAux
        
        committer = ""
        committerAux = commitInfo.get("committer")
        if committerAux != None:
            committer = committerAux.get("login")
        else:
            committer = committerAux
        
        
        filequantity = len(commitInfo.get("files"))
        deletions = commitInfo.get("stats").get("deletions")
        additions = commitInfo.get("stats").get("additions")
        totalModified = commitInfo.get("stats").get("total")
        if int(totalModified) > 0:
            contentValue = filequantity/totalModified
            contentValue = float(float(filequantity)/float(totalModified))
        else:
            contentValue = float(0)
        
        aux = {
            "sha":sha,
            "author":author,
            "committer":committer,
            "filequantity":filequantity,
            "deletions":deletions,
            "additions":additions,
            "totalModified":totalModified,
            "contentValue":contentValue
        }
        return aux
    else:
        print(commit)


def getprsInfos(pull):
    pr = pull.get("prInfo")
    author = ""
    authorAux = pr.get("user")
    if authorAux != None:
        author = authorAux.get("login")
    else:
        author = authorAux

    mergedby = ""
    mergedbyAux = pr.get("merged_by")
    if mergedbyAux != None:
            mergedby = mergedbyAux.get("login")
    else:
        mergedby = mergedbyAux
    
    number = pull.get("number")
    merged = pr.get("merged")
    filequantity = pr.get("changed_files")
    deletions = pr.get("deletions")
    additions = pr.get("additions")
    prState = pr.get("state")
    merge_commit_sha = pr.get("merge_commit_sha")
    created_at = pr.get("created_at")
    merged_at = pr.get("merged_at")
    totalModified = float(float(deletions)+float(additions))
    if totalModified > 0:
        contentValue = float(filequantity/totalModified)
    else:
        contentValue = float(0)
    aux = {
        "number":int(number),
        "author":author,
        "merged":merged,
        "mergedby":mergedby,
        "filequantity":filequantity,
        "deletions":deletions,
        "additions":additions,
        "prState":prState,
        "mergedInCommit":merge_commit_sha,
        "created_at":created_at,
        "merged_at":merged_at,
        "totalModified":totalModified,
        "contentValue":contentValue
    }
    return aux

def getIssuesCommentsOne(url,owner,repo,authen):
    cyc = cyclops.Cyclops(authen)
    result = cyc.requestOne(url)
    return result

def dictUrlNumber(issue):
    aux = issue.get("comments_url")
    return aux


def dictUrlNumberOne(issue):
    aux = {
        "number":int(issue.get("number")),
        "url":issue.get("comments_url")
    }
    return aux

def dictUrlCommit(commit):
    aux = commit.get("url")
    return aux

def dictUrlCommitOne(commit):
    aux = {
        "sha":commit.get("sha"),
        "url":commit.get("url")
    }
    return aux

def dictUrlPRs(pr):
    aux = pr.get("url")
    return aux

def dictUrlPRsOne(pr):
    aux = {
        "number":pr.get("number"),
        "url":pr.get("url")
    }
    return aux

def extractIssueId(urlIssues):
    urlItem1 = urlIssues.replace("https://","")
    urlItem2 = urlItem1.split("/")
    return urlItem2[5]

def idLinkerIssues(item):
    aux = {}
    print(len(item))
    print(item)
    
    urlItem = item[0].get("url")
    
    urlItem1 = urlItem.replace("https://","")
    urlItem2 = urlItem1.split(".")

    urlpath = urlItem2[2]
    urlpath = urlpath.replace("com/","")
    urlComponents = urlpath.split("/")
    #pulls/commits
    if len(urlComponents) < 6:
        if urlComponents[3] == "pulls":
            aux = {
                "number":int(urlComponents[4]),
                "prInfo":item
            }
        elif urlComponents[3] == "commits":
            aux = {
                "sha":urlComponents[4],
                "commitInfo":item
            }
            
    #comments
    elif len(urlComponents) >= 6:
        if (urlComponents[3] == "issues") and (urlComponents[4] == "comments"):
            issuesUrl = item[0].get("issue_url")
            issuesNumber = extractIssueId(issuesUrl)
            number = int(issuesNumber)
            aux = {
                number:item  
            }

    return aux

def idLinkerCommits(item):
    aux = {}
    
    urlItem = item[0].get("url")
    
    urlItem1 = urlItem.replace("https://","")
    urlItem2 = urlItem1.split(".")

    urlpath = urlItem2[2]
    urlpath = urlpath.replace("com/","")
    urlComponents = urlpath.split("/")
    #pulls/commits
    if len(urlComponents) < 6:
        if urlComponents[3] == "pulls":
            aux = {
                "number":int(urlComponents[4]),
                "prInfo":item
            }
        elif urlComponents[3] == "commits":
            aux = {
                "sha":urlComponents[4],
                "commitInfo":item
            }
            
    #comments
    elif len(urlComponents) >= 6:
        if (urlComponents[3] == "issues") and (urlComponents[4] == "comments"):
            issuesUrl = item[0].get("issue_url")
            issuesNumber = extractIssueId(issuesUrl)
            number = int(issuesNumber)
            aux = {
                number:item  
            }

    return aux

def tuple_generator(nrange):
    blockSizeMax = 700
    fator = int(nrange / blockSizeMax)
    fator += 1
    ini = 0
    final = blockSizeMax
    divsConf = []
    for j in range(fator):
        if final > nrange:
            x = [int(ini), int(nrange)]
        else:
            x = [int(ini), int(final)]
        divsConf.append(x)
        ini = final
        final += blockSizeMax
    return divsConf

def getIssuesCommentsList(issueList,owner,repo,authen):
    cyc = cyclops.Cyclops(authen)
    print("get Issues Comments List .......")
    urlList = Parallel(n_jobs=mtp.cpu_count())(delayed(dictUrlNumberOne)(x)for x in issueList)
    subArrays = tuple_generator(len(issueList))
    arraySwap = []
    for index in subArrays:
        print(("sub array {}:{}".format(index[0],index[1])))
        result = cyc.requestMany(urlList[index[0]:index[1]],"issues")
        arraySwap.append(result)
    response = list(chain.from_iterable(arraySwap[i] for i in range(len(arraySwap))))
    resultList = {}
    for item in response:
        if item != []:
            resultList[item.get("number")] = item.get("comments")

    return resultList

def getCommitInfoList(commitList,owner,repo,authen):
    cyc = cyclops.Cyclops(authen)
    print("get commits Info List .......")
    urlList = Parallel(n_jobs=mtp.cpu_count())(delayed(dictUrlCommitOne)(x)for x in commitList)
    subArrays = tuple_generator(len(commitList))
    arraySwap = []
    for index in subArrays:
        print(("sub array {}:{}".format(index[0],index[1])))
        result = cyc.requestMany(urlList[index[0]:index[1]],"commits")
        arraySwap.append(result)
    
    response = list(chain.from_iterable(arraySwap[i] for i in range(len(arraySwap))))
    commitsList = Parallel(n_jobs=mtp.cpu_count())(delayed(getcommitsInfos)(x)for x in response)

    return commitsList

def getPRInfoList(prList,owner,repo,authen):
    cyc = cyclops.Cyclops(authen)
    print("get commits Info List .......")
    urlList = Parallel(n_jobs=mtp.cpu_count())(delayed(dictUrlPRsOne)(x)for x in prList)
    subArrays = tuple_generator(len(prList))

    
    arraySwap = []
    for index in subArrays:
        print(("sub array {}:{}".format(index[0],index[1])))
        try:
            result = cyc.requestMany(urlList[int(index[0]):int(index[1])],"prs")
        except TypeError as e:
            print(index)
            result = []
            print('I got a TypeError - reason "%s"' % str(e))
            pass
        arraySwap.append(result)
    
    response = list(chain.from_iterable(arraySwap[i] for i in range(len(arraySwap))))

    print(len(response))
    prsList = Parallel(n_jobs=mtp.cpu_count())(delayed(getprsInfos)(x)for x in response)
    return prsList
