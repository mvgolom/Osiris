#!/usr/bin/python
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
import multiprocessing as mtp
from itertools import chain
from itertools import cycle
import pathos.pools as mp

class followers:
    def __init__(self,authens,qt_threads=mtp.cpu_count()):
        self.clientAuths = cycle(authens)
        self.clientInfo = next(self.clientAuths)
        self.rate_limit_remaining = 0
        self.rate_limit_reset = 0
        self.num_threads = qt_threads
    

    def range_max_verify(self, url):
        try:
            
            response = urllib.request.urlopen(url)

            header = response.info()
            rangeMax = self.get_pages_range_max(header)
            
            return int(rangeMax)

        except urllib.error.URLError as error:
            if 'HTTP Error 404' in error:
                self.wait_internet_connection(request, parameters)

            with open('error.log', 'a') as error_file:
                error_file.write('Found a error in request: \n')

                if parameters is None:
                    error_file.write('https://api.github.com/' + request + 'per_page=100&client_id=' +
                                        self.id + '&client_secret=' + self.secret + '\n')
                else:
                    error_file.write('https://api.github.com/' + request + '?per_page=100&client_id=' + self.id +
                                        '&client_secret=' + self.secret +
                                        '&' + '&'.join(parameters) + '\n')
                error_file.write('Error type: ' + str(error) + '\n\n')
            pass


    def get_pages_range_max(self,header):
        page_range = ""
        print("\n")
        print(header)
        print("\n")
        if "link" in header:
            for item in list(header.items()):
                print(item)
                if 'link' in item:
                    page_range = item[1]

                    page_range = page_range.replace('; rel="last"','')
                    page_range = page_range.replace(">",'')
                    page_range = page_range.replace("<",'')
                    page_range_link = page_range.split(",")
                    

                    link_components = urllib.parse.urlparse(page_range_link[1])
                    link_components = urllib.parse.parse_qs(urllib.parse.urlsplit(page_range_link[1]).query)
                    
                    max_range = "".join(link_components["page"])
                else:
                    max_range = 1
        else:
            max_range = 1
        
        return int(max_range)

    def byteify(self, input):
        if isinstance(input, dict):
            return {self.byteify(key): self.byteify(value)
                    for key, value in input.items()}
        elif isinstance(input, list):
            return [self.byteify(element) for element in input]
        elif isinstance(input, str):
            return input.encode('utf-8')
        else:
            return input


    def requester(self, item):
        flag = False
        params = ['page=' + str(item.get("index"))]
        urlf = item.get("url")+"&"+"&".join(params)
        body = {}
        try:
            response = urllib.request.urlopen(urlf)
            header = response.info()
            body = json.load(response)
        except urllib.error.URLError:
            body = []
            pass
        
        return body


    def verify_rate_limit(self, header, name):
            self.clientAuths
            self.clientInfo
            self.rate_limit_remaining
            self.rate_limit_reset
            for item in list(header.items()):
                if 'x-ratelimit-remaining' in item:
                    rate_limit_remaining = int(item[1])
                if 'x-ratelimit-reset' in item:
                    rate_limit_reset = int(item[1])

            datetime_format = '%Y-%m-%d %H:%M:%S'
            datetime_reset = datetime.datetime.fromtimestamp(rate_limit_reset).strftime(datetime_format)
            datetime_now = datetime.datetime.now().strftime(datetime_format)

            print('[API] Requests Remaining:' + str(rate_limit_remaining))

            if rate_limit_remaining <= 50:
                clientCredencials = next(clientAuths)
                clientAuths = clientCredencials
                return True
            else:
                return False

    def getFollowers(self, name):
        auths = self.clientInfo
        bodyEmpty = False
        url = 'https://api.github.com/users/'+name+'/followers'+'?per_page=100&client_id='+auths["client_id"]+\
        '&client_secret='+auths["client_secret"]

        results_list = []

        response = urllib.request.urlopen(url)

        header = response.info()
        num_pages = self.get_pages_range_max(header)

        urlList = [{"url":url,"index":x+1} for x in range(0,num_pages)]
        p =  mp.ThreadPool(self.num_threads)
        if num_pages > 1:
            results_list = p.map(self.requester, urlList)
            print(len(results_list))
            flag = self.verify_rate_limit(header,name)
            if flag == True:
                url = 'https://api.github.com/users/'+name+'/following'+'?per_page=100&client_id='+self.clientInfo["client_id"]+\
                    '&client_secret='+self.clientInfo["client_secret"]
        else:
            response = urllib.request.urlopen(url)
            body = json.load(response)
            if body != []:
                results_list.append(self.byteify(body))
            else:
                bodyEmpty = True
        
        if bodyEmpty == False:
            followers = list(chain.from_iterable(results_list[i] for i in range(len(results_list))))
            return len(followers)
        else:
            return 0

    def getFollowersLazy(self, name):
        print("followers -> {}".format(name))
        auths = self.clientInfo
        print(auths["client_id"])
        print(auths["client_secret"])
        print("\n")
        bodyEmpty = False
        url = 'https://api.github.com/users/'+name+'/followers'+'?per_page=100&client_id='+auths["client_id"]+\
        '&client_secret='+auths["client_secret"]

        results_list = []
        try:
            response = urllib.request.urlopen(url)
        except urllib.error.HTTPError as e:
            response = []
            print(e.fp.read())
            pass

        header = response.info()
        num_pages = self.get_pages_range_max(header)

        if(num_pages > 1):
            lastPage = num_pages
            fullPages = num_pages-1
            fullPages = fullPages*30

            params = ("page={}").format(lastPage)

            urlf = ("{}&{}").format(url,params)
            try:
                response = urllib.request.urlopen(urlf)
            except urllib.error.HTTPError as e:
                print(e.fp.read())
                pass

            body = json.load(response)
            lastPageTam = len(body)
            countFinal = fullPages+lastPageTam
            aux = {"login":name,"followers":countFinal}
            return aux
        else:
            try:
                response = urllib.request.urlopen(url)
            except urllib.error.HTTPError as e:
                print(e.fp.read())
                pass

            body = json.load(response)
            if body != []:
                aux = {"login":name,"followers":len(body)}
                return aux
            else:
                aux = {"login":name,"followers":0}
                return aux



    def getFollowing(self, name):
        auths = self.clientInfo
        flag = False
        bodyEmpty = False
        url = 'https://api.github.com/users/'+name+'/following'+'?per_page=100&client_id='+auths["client_id"]+\
        '&client_secret='+auths["client_secret"]

        results_list = []

        response = urllib.request.urlopen(url)

        header = response.info()
        num_pages = self.get_pages_range_max(header)

        print("qtd de pages: "+str(num_pages))
        urlList = [{"url":url,"index":x+1} for x in range(0,num_pages)]
        p =  mp.ThreadPool(self.num_threads)
        if num_pages > 1:
            results_list = p.map(self.requester, urlList)

            flag = self.verify_rate_limit(header,name)
            if flag == True:
                url = 'https://api.github.com/users/'+name+'/following'+'?per_page=100&client_id='+self.clientInfo["client_id"]+\
                    '&client_secret='+self.clientInfo["client_secret"]
        else:
            response = urllib.request.urlopen(url)
            body = json.load(response)
            if body != []:
                results_list.append(self.byteify(body))
            else:
                bodyEmpty = True
        if bodyEmpty == False:
            followings = list(chain.from_iterable(results_list[i] for i in range(len(results_list))))
            return self.byteify(followings)
        else:
            return 0

    def getLogin(self, userObj):
        if userObj != "[]":
            try:
                login = userObj["login"]
                return login
            except KeyError as e:
                print('I got a KeyError - reason "%s"' % str(e))
            except IndexError as e:
                print('I got an IndexError - reason "%s"' % str(e))

    def followingsList(self, login):
        followings = self.getFollowing(login)
        p =  mp.ThreadPool(self.num_threads)
        if followings != 0:
            results = p.map(self.getLogin, followings)
        else:
            results = 0
        
        return results 

    def followers(self, login):
        followers = self.getFollowers(login)
        return followers

    def followersList(self, listLogin):
        p =  mp.ThreadPool(self.num_threads)
        followings = [x.get("login") for x in listLogin if x.get("login") != None]
        followersfinal = p.map(self.getFollowersLazy, followings)
        aux = {}
        for x in followersfinal:
            aux[x["login"]] = x["followers"] 
        return aux
