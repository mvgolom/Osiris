import re
import sys
import json
import time
import datetime
import requests
import unicodedata
import multiprocessing as mp
import pymongo as Pymongo
from itertools import chain
from collections import Counter
from pymongo import MongoClient
from joblib import Parallel, delayed

projectUserAssociation = {'COMMITTER': 'committers', 'MEMBER': 'members',
                          'OWNER': 'owner', 'CONTRIBUTOR': 'contributors', 'COLLABORATOR': 'collaborators'}




def createInit():
    print('Create and Intializing ........')
    databases_names = ['global_metrics', 'global_status',
                       'projects', 'global_configs', 'github_credencials']
    conn = MongoClient('localhost', 27017)
    db_names = conn.database_names()
    for db_name in databases_names:
        if bool(db_name in db_names):
            print("Base {} found".format(db_name))
        elif 'global_status' == db_name:
            db = conn[db_name]
            index_name = 'uniqueLogin'
            my_collection = db['global_status_names']
            my_collection.create_index(
                [('login', 1)], name=index_name, unique=True)
            print('Base {} create'.format(db_name))
        elif 'global_metrics' == db_name:
            db = conn[db_name]
            index_name = 'uniqueProjectName'
            my_collection = db['projectMetrics']
            my_collection.create_index(
                [('projectName', 1)], name=index_name, unique=True)
            print('Base {} create'.format(db_name))
        elif 'projects' == db_name:
            db = conn[db_name]
            index_name = 'uniqueProjectName'
            my_collection = db['projectsNames']
            my_collection.create_index(
                [('name', 1)], name=index_name, unique=True)
            print('Base {} create'.format(db_name))
        elif 'github_credencials' == db_name:
            db = conn[db_name]
            index_name = 'uniqueProjectName'
            my_collection = db['credencials']
            my_collection.create_index(
                [('client_id', 1)], name=index_name, unique=True)
            print('Base {} create'.format(db_name))
        elif 'global_configs' == db_name:
            db = conn[db_name]
            my_collection = db['configs']
            print('Base {} create'.format(db_name))
            my_collection.insert_one({"operation":"treads_useds","treads_useds":mp.cpu_count()})
            my_collection.insert_one({"operation":"bd_url","bd_url":'localhost'})
            my_collection.insert_one({"operation":"bd_port","bd_port":27017})
            my_collection.insert_one({"operation":"status","status":"OFF"})
            

def DeleteAll():
    conn = MongoClient('localhost', 27017)
    databases_names = ['global_metrics', 'global_status',
                       'projects', 'global_configs', 'github_credencials']
    for db_name in databases_names:
        conn.drop_database(db_name)
        print('Deleted {}'.format(db_name))
