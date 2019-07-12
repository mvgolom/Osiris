import datetime
import time
import json
import sys
from pymongo import MongoClient
import pymongo as Pymongo
import time
from pprint import pprint

connection = MongoClient('localhost', 27017)


def loadJson(path):
    with open(path) as data_file:
        data = json.loads(data_file.read())
    return data


def projectsjson(jsonFile):
    db = connection["projects"]
    projectsDuplicate = []
    for file in jsonFile:
        nameAux = file.get("name")
        visitedAux = file.get("visited")
        try:
            if((visitedAux == True) and (visitedAux != None)):
                db.projectsNames.insert({"name": nameAux, "visited": True})
            else:
                db.projectsNames.insert({"name": nameAux, "visited": False})
        except Pymongo.errors.DuplicateKeyError:
            projectsDuplicate.append(file)
            continue
    if(len(projectsDuplicate) > 0):
        print("Duplicate projects {}".format(len(projectsDuplicate)))
        if(len(projectsDuplicate) < 100):
            pprint(projectsDuplicate)
        elif(len(projectsDuplicate) > 100):
            pprint(projectsDuplicate[0:100])
            print("........")
        with open("./log/projectsDuplicate.json", "a") as fp:
            json.dump(projectsDuplicate, fp)

    return (len(jsonFile) - len(projectsDuplicate))


def keysJson(jsonFile):
    db = connection["github_credencials"]
    credencialsDuplicate = []
    for file in jsonFile:
        client_id = file.get('client_id')
        client_secret = file.get('client_secret')
        try:
            db.credencials.insert({"client_id": client_id, "client_secret": client_secret})
        except Pymongo.errors.DuplicateKeyError:
            credencialsDuplicate.append(file)
            continue
    if(len(credencialsDuplicate) > 0):
        print("Duplicate Keys {}".format(len(credencialsDuplicate)))
        if(len(credencialsDuplicate) < 100):
            pprint(credencialsDuplicate)
        elif(len(credencialsDuplicate) > 100):
            pprint(credencialsDuplicate[0:100])
            print("........")
        with open("./log/credencialsDuplicate.json", "a") as fp:
            json.dump(credencialsDuplicate, fp)

    return (len(jsonFile) - len(credencialsDuplicate))

def projectsCompleted():
    db = connection["projects"]
    projectsName = list(db.projectsNames.find({"visited":{"$eq":True}}))
    print("Projects Finished {}".format(len(projectsName)))

def projectsLen():
    db = connection["projects"]
    projectsName = list(db.projectsNames.find({}))
    print("Total Projects {}".format(len(projectsName)))

def keysLen():
    db = connection["github_credencials"]
    keys = list(db.credencials.find({}))
    print("Total GitHub Keys {}".format(len(keys)))

def statusCrawler():
    statusCrawler = connection["global_configs"]
    status = statusCrawler.configs.find_one({"operation":"status"},{"_id":0})
    print("Crawler Status {}".format(status.get("status")))


def main():
    oneArgument = ["--finished","--projects","--keys","--status"]
    if (len(sys.argv) <= 2) and (sys.argv[1] not in oneArgument):
	    print('missing arguments')
	    raise SystemExit

    if(sys.argv[1] == "--projects"):
        if(len(sys.argv) <= 2):
            projectsLen()
        else:
            myjson=loadJson(sys.argv[2])
            if(len(myjson) == 1):
                myjson=[myjson]
            inserted=projectsjson(myjson)
            print("{} inserted projects in BD".format(inserted))

    elif(sys.argv[1] == "--keys"):
        if(len(sys.argv) <= 2):
            keysLen()
        else:
            myjson=loadJson(sys.argv[2])
            if(len(myjson) == 1):
                myjson=[myjson]
            inserted=keysJson(myjson)
            print("{} inserted keys in BD".format(inserted))

    elif(sys.argv[1] == "--finished"):
        projectsCompleted()
    
    elif(sys.argv[1] == "--status"):
        statusCrawler()
        projectsLen()
        projectsCompleted()
        keysLen()
    else:
        print("{} option not allowed".format(sys.argv[1]))

if __name__ == '__main__':
    main()
