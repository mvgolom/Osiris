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
from pprint import pprint
try:
    from CrawlerLibs import follow, cyclopslair
except ImportError as error:
    raise ImportError(error)

def statusInProject():
    client = MongoClient('localhost', 27017)
    db = client["global_metrics"]
    db2 = client["global_status"]
    db3 = client["global_metrics_final"]
    
    allMetrics = list(db.projectMetrics.find({},{"_id":0}))
    print(len(allMetrics))
    auxstate = list(db2.global_status_names.find({}))
    auxStatusGlobal = []
    for projectState in auxstate:
         auxStatusGlobal.append(projectState.get("login"))

    print(len(auxStatusGlobal))

    statusGlobal = {}
    
    for status in auxstate:
        loginStatus = status.get("login")
        qtProject = status.get("qtProject")
        statusGlobal[loginStatus] = qtProject

    
    for repoMetrics in allMetrics:
        projectName = repoMetrics.get("projectName")
        pprint(repoMetrics)
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