import datetime,time
from flask import Flask, session, request, render_template, redirect, url_for, Response
import json
import sys
from pymongo import MongoClient
from flask_cors import CORS
from flask_misaka import Misaka
import pymongo as Pymongo
import time

app = Flask(__name__)
cors = CORS(app, resources={r"/*": {"origins": "*"}})
Misaka(app)

connection = MongoClient('localhost', 27017)


def human_format(num):
    num = float('{:.3g}'.format(num))
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    return '{}{}'.format('{:f}'.format(num).rstrip('0').rstrip('.'), ['', 'K', 'M', 'B', 'T'][magnitude])

def json_response(payload, status=200):
    return (json.dumps(payload), status, {'content-type': 'application/json'})

@app.route("/")
def index():
    content = ""
    with open("README.md", "r") as f:
        content = f.read()
    return render_template("index.html", text = content)

@app.route("/status/crawler")
def status():
    if(request.method == "GET"):
        statusCrawler = connection["global_configs"]
        content = statusCrawler.configs.find_one({"operation":"status"},{"_id":0})
        return json_response(content)


@app.route("/projects",methods=['POST','GET'])
def projects():
    if(request.method == "GET"):
        db = connection["projects"]
        aux = list(db.projectsNames.find({},{"_id":0}))
        duplicate = list(db.projectsDuplicate.find({},{"_id":0}))
        db.projectsDuplicate.delete_many({})
        qt = human_format(len(aux))
        auxDict = {
            "qt":qt,
            "projects":aux,
            "duplicate":duplicate
        }
        return render_template("projects.html", content = auxDict)
    elif(request.method == "POST"):
        return redirect("/")

@app.route("/projects/add",methods=['POST','GET'])
def projectsAdd():
    if(request.method == "POST"):
        repo = request.form.get('repo')
        repo = repo.strip()
        db = connection["projects"]
        try:
            db.projectsNames.insert({"name":repo,"visited":False})
        except Pymongo.errors.DuplicateKeyError:
            db.projectsDuplicate.insert({"name":repo,"visited":False})
            pass
        return redirect("/projects")

    elif(request.method == "GET"):
        return redirect("/")

@app.route("/projects/addjson",methods=['POST','GET'])
def projectsjson():
    if request.method == "POST":
        repo = request.files.get('file')
        myfile = repo.read()
        jsonFile = json.loads(myfile)
        print(jsonFile)
        db = connection["projects"]
        for file in jsonFile:
            nameAux = file.get("name")
            visitedAux = file.get("visited")
            try:
                if((visitedAux == True) and (visitedAux != None)):
                    db.projectsNames.insert({"name":nameAux,"visited":True})
                else:
                    db.projectsNames.insert({"name":nameAux,"visited":False})
            except Pymongo.errors.DuplicateKeyError:
                db.projectsDuplicate.insert({"name":nameAux,"visited":False})
                continue
        return redirect("/projects")
    
    elif request.method == "GET" :
        return redirect("/")

@app.route("/projects/del",methods=['POST','GET'])
def delproject():
    if request.method == "POST":
        db = connection["projects"]
        repo = request.form.get('repo')
        try:
            db.projectsNames.delete_one({"name":repo})
        except Pymongo.errors.OperationFailure as e:
            print(e)
            pass
        return redirect("/projects")
    elif request.method == "GET" :
        return redirect("/")

@app.route("/projects/edit",methods=['POST','GET'])
def editproject():
    if request.method == "POST":
        repo = request.form.get('repo')
        newRepo = request.form.get('newrepo')
        repo = repo.strip()
        print(repo)
        db = connection["projects"]
        try:
            db.projectsNames.update({"name":repo},{"$set":{"name":newRepo}})
        except Pymongo.errors.OperationFailure as e:
            print(e)
            pass
        return redirect("/projects")
    elif request.method == "GET" :
        return redirect("/")


@app.route("/keys",methods=['POST','GET'])
def keys():
    if(request.method == "GET"):
        db = connection["github_credencials"]
        aux = list(db.credencials.find({},{"_id":0}))
        duplicate = list(db.credencialsDuplicate.find({},{"_id":0}))
        db.credencialsDuplicate.delete_many({})
        auxDict = {
            "clients":aux,
            "duplicate":duplicate
        }
        return render_template("keys.html", content = auxDict)
    
    elif(request.method == "POST"):
        return redirect("/")

@app.route("/keys/add",methods=['POST','GET'])
def keysAdd():
    if(request.method == "POST"):
        db = connection["github_credencials"]
        client_id = request.form.get('client_id')
        client_secret = request.form.get('client_secret')
        client_id = client_id.strip()
        client_secret = client_secret.strip()
        try:
            db.credencials.insert({"client_id":client_id,"client_secret":client_secret})
        except Pymongo.errors.DuplicateKeyError:
            db.credencialsDuplicate.insert({"client_id":client_id,"client_secret":client_secret})
            pass
        return redirect("/keys")
    elif(request.method == "GET"):
        return redirect("/")

# send file
@app.route("/keys/addjson",methods=['POST','GET'])
def keysJson():
    if request.method == "POST":
        jsonkeys = request.files.get('file')
        myfile = jsonkeys.read()
        jsonFile = json.loads(myfile)
        db = connection["github_credencials"]
        for file in jsonFile:
            client_id = file.get('client_id')
            client_secret = file.get('client_secret')
            try:
                db.credencials.insert({"client_id":client_id,"client_secret":client_secret})
            except Pymongo.errors.DuplicateKeyError:
                db.credencialsDuplicate.insert({"client_id":client_id,"client_secret":client_secret})
                continue
        return redirect("/keys")
    
    elif request.method == "GET" :
        return redirect("/")

@app.route("/keys/del",methods=['POST','GET'])
def delkey():
    if request.method == "POST":
        db = connection["github_credencials"]
        client_id = request.form.get('client_id')
        client_secret = request.form.get('client_secret')
        try:
            db.credencials.delete_one({"client_id":client_id})
        except Pymongo.errors.OperationFailure as e:
            print(e)
            pass
        return redirect("/keys")
    elif request.method == "GET" :
        return redirect("/")

@app.route("/keys/edit",methods=['POST','GET'])
def editkey():
    if request.method == "POST":
        client_id = request.form.get('client_id')
        newClient_id = request.form.get('newClient_id')
        client_secret = request.form.get('client_secret')
        newClient_secret = request.form.get('newClient_secret')
        db = connection["github_credencials"]
        try:
            if(client_id != newClient_id):
                db.credencials.update({"client_id":client_id},{"$set":{"client_id":newClient_id}})
            if(client_secret != newClient_secret):
                db.credencials.update({"client_secret":client_secret},{"$set":{"client_secret":newClient_secret}})
        except Pymongo.errors.OperationFailure as e:
            print(e)
            pass
        return redirect("/keys")
    elif request.method == "GET" :
        return redirect("/")

@app.route("/configs",methods=['POST','GET'])
def configs():
    db = connection["global_configs"]
    configsList = list(db.configs.find({},{"_id":0,"operation":0}))
    auxDict ={}
    for item in configsList:
        itemkey = list(item)[0]
        auxDict[itemkey] = item[itemkey]
    print(auxDict)
    return render_template("configs.html", content = auxDict)

@app.route("/configs/edit",methods=['POST','GET'])
def editConfig():
    if request.method == "POST":
        config = request.form.get('configname')
        configValue = request.form.get('configValue')
        newConfigValue = request.form.get('newconfigValue')
        newConfigValue = newConfigValue.strip()
        db = connection["global_configs"]
        if(config == "treads_useds"):
            try:
                threadNum = int(newConfigValue)
                teste = db.configs.update({"operation":config},{"$set":{"treads_useds":threadNum}})
                print(teste)
            except Pymongo.errors.OperationFailure as e:
                print(e)
                pass
        elif(config == "bd_url"):
            try:
                teste = db.configs.update({"operation":config},{"$set":{"bd_url":newConfigValue}})
                print(teste)
            except Pymongo.errors.OperationFailure as e:
                print(e)
                pass
        elif(config == "bd_port"):
            try:
                bd_port = int(newConfigValue)
                teste = db.configs.update({"operation":config},{"$set":{"bd_port":bd_port}})
                print(teste)
            except Pymongo.errors.OperationFailure as e:
                print(e)
                pass
        return redirect("/configs")
    elif request.method == "GET" :
        return redirect("/")


if __name__ == "__main__":
    app.jinja_env.cache = {}
    app.run(debug=True)