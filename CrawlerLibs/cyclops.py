#!/usr/bin/python
# -*- coding: utf-8 -*-
#Author: Marcos Golom
#Contact: viniciusgolom@gmail.com

import json
import time
import joblib
import urllib.request, urllib.error, urllib.parse
import datetime
import urllib.parse
import requests
import multiprocessing as mtp
from pathos.pools import ParallelPool as Pool
from functools import partial
from itertools import chain
from itertools import cycle
import pathos.pools as mp
from joblib import Parallel, delayed
from pymongo import MongoClient

class Cyclops:
    def __init__(self,authens,qt_threads=mtp.cpu_count()):
        self.clientAuths = cycle(authens)
        self.clientInfo = next(self.clientAuths)
        self.client_id = self.clientInfo.get("client_id")          
        self.client_secret = self.clientInfo.get("client_secret")
        self.x_RateLimit_Limit = 5000
        self.x_RateLimit_Remaining = 0
        self.x_RateLimit_Reset = 0
        self.num_threads = qt_threads
        

    def multiRequester(self,index,url):
        while True:
            credencial = '?client_id='+self.client_id+'&client_secret='+self.client_secret
            urlf = ("{}{}").format(url,credencial)
            urlf2 = "{}&page={}".format(urlf,index)
            # print("{}&page={}").format(url,index)
            response = requests.get(urlf2)
            header = response.headers
            self.verifyRequestLimit(header)
            if int(response.status_code) == 200:
                break
            elif int(response.status_code) == 403:
                self.rollAuths()

        body = response.json()
        return body

    def requester(self,url):
        results_list = []
        while True:
            credencial = '?per_page=100&client_id='+self.client_id+'&client_secret='+self.client_secret
            urlf = ("{}{}").format(url,credencial)
            response = requests.get(urlf)
            header = response.headers
            self.verifyRequestLimit(header)
            if int(response.status_code) == 200:
                break
            elif int(response.status_code) == 403:
                self.rollAuths()

        body = response.json()
        if body != []:
            results_list.append(body)
            return body
        else:
            final = []
            return final
    
    def requesterIssueComments(self,url):
        print(("{}:{}").format(url.get("number"),url.get("url")))
        while True:
            credencial = '?per_page=100&client_id='+self.client_id+'&client_secret='+self.client_secret
            urlf = ("{}{}").format(url.get("url"),credencial)
            response = requests.get(urlf)
            header = response.headers
            self.verifyRequestLimit(header)
            if int(response.status_code) == 200:
                break
            elif int(response.status_code) == 403:
                self.rollAuths()

        body = response.json()
        if body != []:
            aux = {
                "number":int(url.get("number")),
                "comments":body
            }
            return aux
        else:
            final = []
            return final
    
    def requesterCommitInfo(self,commit):
        # print("{} : {}").format("commit",commit.get("sha"))
        while True:
            credencial = '?per_page=100&client_id='+self.client_id+'&client_secret='+self.client_secret
            urlf = ("{}{}").format(commit.get("url"),credencial) 
            response = requests.get(urlf)
            header = response.headers
            self.verifyRequestLimit(header)
            if int(response.status_code) == 200:
                break
            elif int(response.status_code) == 403:
                self.rollAuths()
        
        body = response.json()
        if body != []:
            aux = {
                "sha":commit.get("sha"),
                "commitInfo":body
            }
            return aux
        else:
            final = []
            return final

    def requesterPRInfo(self,pr):
        # print("{} : {}").format("Pull Request",pr.get("number"))
        while True:
            credencial = '?per_page=100&client_id='+self.client_id+'&client_secret='+self.client_secret
            urlf = ("{}{}").format(pr.get("url"),credencial)
            response = requests.get(urlf)
            header = response.headers
            self.verifyRequestLimit(header)
            if int(response.status_code) == 200:
                break
            elif int(response.status_code) == 403:
                self.rollAuths()

        body = response.json()
        if body != []:
            aux = {
                "number":pr.get("number"),
                "prInfo":body
            }
            return aux
        else:
            final = []
            return final

    #get request of 1 page with many return pages
    def requestOne(self,url,raw=False):
        results_list = []
        bodyEmpty = False
        #connection test and reconnect

        while True:
            urlBase = "https://api.github.com/"
            credencial = '?per_page=100&client_id='+self.client_id+'&client_secret='+self.client_secret
            urlf = ("{}{}").format(urlBase,credencial)
            response = requests.get(urlf)
            header = response.headers
            self.verifyRequestLimit(header)
            if int(response.status_code) == 200:
                break
            if int(response.status_code) == 404:
                self.wait_for_internet_connection()
        
        numPages = self.getRange(url)
        p =  mp.ThreadPool(self.num_threads)
        if(numPages > 1):
            results_list = p.map(partial(self.multiRequester, url=url), list(range(1,numPages+1)))
        else:
            response = self.requester(url)
            if response != -1:
                results_list.append(response)
            else:
                bodyEmpty = True

        self.getRange(url)

        if ((bodyEmpty == False) and (raw == False)):
            response = list(chain.from_iterable(results_list[i] for i in range(len(results_list))))
            return response
        elif(raw == True):
            return response
        else:
            final = []
            return final 

    def requestMany(self,urlList,category):
        print("request Many in once .....")
        results_list = []
        bodyEmpty = False

        #reconnection
        while True:
            urlBase = "https://api.github.com/repos/mvgolom/letroca/commits"
            credencial = '?per_page=100&client_id='+self.client_id+'&client_secret='+self.client_secret
            urlf = ("{}{}").format(urlBase,credencial)
            response = requests.get(urlf)
            header = response.headers
            self.verifyRequestLimit(header)
            if int(response.status_code) == 200:
                break
            if int(response.status_code) == 404:
                self.wait_for_internet_connection()

        p =  mp.ThreadPool(self.num_threads)
        if(category == "issues"):
            try:
                results_list = p.map(self.requesterIssueComments, urlList)
            except TypeError as e:
                #print urlList
                print('I got a TypeError - reason "%s"' % str(e))
        elif(category == "commits"):
            try:
                results_list = p.map(self.requesterCommitInfo, urlList)
            except TypeError as e:
                print(urlList)
                print('I got a TypeError - reason "%s"' % str(e))
        elif(category == "prs"):
            try:
                results_list = p.map(self.requesterPRInfo, urlList)
            except TypeError as e:
                print(urlList)
                print('I got a TypeError - reason "%s"' % str(e))

        return results_list


    def getLimitRemaining(self,header):
        RateLimit_Remaining = 0
        for item in list(header.items()):
            if 'x-ratelimit-remaining' in item:
                RateLimit_Remaining = int(item[1])
        return RateLimit_Remaining

    def getlimitReset(self):
        return self.x_RateLimit_Reset
    
    def getLimitRemaining(self,header):
        RateLimit_Remaining = header.get("X-RateLimit-Remaining")
        return int(RateLimit_Remaining)

    def rollAuths(self):
        print ("Credencials Updated !!!!!")
        print("[Cyclops] RateLimit Remaining: {}".format(self.x_RateLimit_Remaining))
        self.clientCredencials = next(self.clientAuths)
        self.clientInfo = self.clientCredencials
        
        self.client_id = self.clientInfo.get("client_id")
        self.client_secret = self.clientInfo.get("client_secret")
        print(("{}:{}").format(self.client_id,self.client_secret))


    def verifyRequestLimit(self, header,limit=None):
        self.clientInfo
        self.x_RateLimit_Remaining = int(header.get("X-RateLimit-Remaining"))
        self.x_RateLimit_Reset = int(header.get("X-ratelimit-reset"))
        dateTimeFormat = '%Y-%m-%d %H:%M:%S'
            
        datetime_now = datetime.datetime.now().strftime(dateTimeFormat)
        if self.x_RateLimit_Remaining <= 700:
            self.rollAuths()
            urlBase = "https://api.github.com/"
            credencial = '?per_page=100&client_id='+self.client_id+'&client_secret='+self.client_secret
            urlf = ("{}{}").format(urlBase,credencial)
            response = requests.get(urlf)
            header = response.headers
            remaining = self.getLimitRemaining(header)
            if remaining > 700:
                print ("Credencials Updated !!!!!")

    def getRange(self,url):
        credencial = '?per_page=100&client_id='+self.client_id+'&client_secret='+self.client_secret
        urlf = ("{}{}").format(url,credencial)
        response = urllib.request.urlopen(urlf)
        header = response.info()
        return self.getPagesRange(header)

    #get number of pages
    def getPagesRange(self,header):
        page_range = ""
        if "link" in header:
            for item in list(header.items()):
                if 'link' in item:
                    page_range = item[1]
            
            page_range = page_range.replace('; rel="last"','')
            page_range = page_range.replace(">",'')
            page_range = page_range.replace("<",'')
            page_range_link = page_range.split(",")

            link_components = urllib.parse.urlparse(page_range_link[1])
            link_components = urllib.parse.parse_qs(urllib.parse.urlsplit(page_range_link[1]).query)
            
            max_range = "".join(link_components.get("page"))
        else:
            max_range = 1
        
        return int(max_range)

    #connection handler
    def wait_for_internet_connection(self):
        while True:
            try:
                response = urllib.request.urlopen('https://dns.google.com/resolve?name=example',timeout=1)
                return
            except urllib.error.URLError:
                time.sleep(10)
                pass
