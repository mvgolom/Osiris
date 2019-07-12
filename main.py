#!/usr/bin/python
# -*- coding: utf-8 -*-
import re
import sys
import json
import time
import DataBase
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
from Metrics import metrics
from DataBase import actions as act

def main():
    try:
        client = MongoClient('localhost', 27017)
    except e:
        print(e)
        raise
    
    db = client["projects"]
    db2 = client["github_credencials"]
    authentication = list(db2.credencials.find({},{"_id":0}))
    projectsName = list(db.projectsNames.find({"visited":{"$eq":False}}))
    name = {"name":"davisking/dlib","visited":False}
    # name = {"name":"egoist/yarn-create-vue-app","visited":False}
    projectsName = [name]
    try:
        statusCrawler = client["global_configs"]
        statusCrawler.configs.update({"operation":"status"},{"$set":{"status":"ON"}})
        for project in projectsName:
            db_names = client.database_names()
            name = project.get("name")
            arg = name.split("/")
            owner = arg[0]
            repo = arg[1]
            namerepo = ""
            flag404 = False
            if "." in arg[1]:
                namerepo = arg[1].replace(".","")
            else:
                namerepo = arg[1]
            
            dbname = (namerepo+"_metrics")

            if len(namerepo) >= 64:
                namerepo = namerepo[0:62]
            
            print( "{}:{}".format(owner,namerepo))
            #if namerepo in db_names:
            #    client.drop_database(namerepo)
            #if dbname in db_names:
            #    client.drop_database(dbname)
            
            now = datetime.datetime.now()
            print( ("{}:{}:{}").format(now.hour,now.minute,now.second))
            url = ("https://api.github.com/repos/{}/{}/commits?&client_id={}&client_secret={}").format(owner,repo,authentication[0].get("client_id"),authentication[0].get("client_secret"))
            rqt404 = requests.get(url)
            statusCode = int(rqt404.status_code)
            
            aux = rqt404.json()
            try:
                msg = aux.get("message")
                if("is empty" in msg):
                    flag404 = True
            except AttributeError:
                pass
            except TypeError:
                print("TypeError msg")
                pass
            
            if (statusCode == 404):
                aux = rqt404.json()
                msg = aux.get("message")
                try:
                    if("Not Found" in msg):
                        flag404 = True
                except( TypeError, e):
                    print ("TypeError msg")
                    pass

            if(flag404 != True):
                """"Get All Commits,Issues,PRs and Contributors"""
                
                #ext.getInfo(name,authentication)
                """Get all Contributors, Owner, Members and Committers"""
                ext.getAllContributors(owner,namerepo)
                #ext.ownerSearch(owner,namerepo,name,authentication)
                """Get All Comments in Repository Issues and PRs """
                
                #ext.getAllCommentsTypes(owner,namerepo,authentication)
                """Get Code Information """
                #ext.codeGetterInfo(owner,namerepo,authentication)
                print( "Working in Metrics .....")

                #metrics.closenessOwner(owner,namerepo,authentication)
                #metrics.status(owner,namerepo,authentication)
                #metrics.ParticipationWcode(owner,namerepo,authentication)
                #metrics.participationWComments(owner,namerepo,authentication)
                #metrics.contentValueInProject(owner,namerepo,authentication)
                #metrics.sourceOfLearning(owner,namerepo,authentication)
                #metrics.longTimeInteractionWproject(owner,namerepo,authentication)
                #act.statusGlobalSave(owner,namerepo)
                #act.archiveProject(owner,repo,namerepo)
                #db.projectsNames.update({"name":name},{"$set":{"visited":True}})
            else:
                now = datetime.datetime.now()
                date = "{}:{}:{}".format(now.hour,now.minute,now.second)
                log = {
                    "name": name,
                    "date": date
                }
                with open("./log/logNotFound.txt.json","a") as fp:
                    json.dump(log, fp)
                db.projectsNames.update({"name":name},{"$set":{"visited":True}}) 
            

            # statusInProject()
            now = datetime.datetime.now()
            print( ("{}:{}:{}").format(now.hour,now.minute,now.second))
    finally:
        statusCrawler = client["global_configs"]
        statusCrawler.configs.update({"operation":"status"},{"$set":{"status":"OFF"}})

if __name__ == '__main__':
    main()