# -*- coding: utf-8 -*-
"""
Created on Wed Apr 13 2016

@author: D. Temkin
"""
from bs4 import BeautifulSoup as bsoup
from collections import Counter
from scipy import stats
from time import sleep
import requests
import json
import sqlite3
import numpy
import re
import os
import string 
import pygal

fullpath= lambda x: os.path.abspath(os.path.join(os.path.dirname(__file__), x))



sqlfile = fullpath("main.db")
conn = sqlite3.connect(sqlfile)
curs = conn.cursor()


class Ratings:


    def __init__(self, api, apikey=None):
        self.review_url = None
        self.api = api
        self.apikey = apikey
        self.useragent = # REQUIRED-- Check out my github repo @ github.com/just-dantastic/useragent-hoodini
        self.rawscore, self.review_sent = None, None
        self.data = []
        
    def _format_title(self, x, y):
        title = re.sub('[%s]' % re.escape(string.punctuation), '', x.lower())

        urlref = str(title + " %s" % y).split()
        urlref = "-".join(urlref)
        return urlref

    def _build_url(self, url, **args):
        args = dict(**args)
        title = args["title"]
        urlext = self._format_title(args["title"], args["year"])
        self.review_url = "".join([url, urlext])


    def observed(self, title, year, titleid):
        
        baseurl = "http://www.rogerebert.com/reviews/"
        
        self._build_url(baseurl, title=title, year=year)
        try:
            req = requests.get(self.review_url, headers={'user-agent':self.useragent})
        except Exception as errmsg:
            
            
            print("Err: %s" % errmsg)
            return False
        else:

            soup = bsoup(req.text, 'html5lib')
            reviewhtml = soup.find("div", {"itemprop":"reviewBody"})
            section = soup.find("section", {"class":"main fixed-rail"})
            article = section.find("article", {"class":"pad entry"})
            head = article.find("header")
            
            starsbase = head.find('span',{'itemprop':"reviewRating", 'itemtype':"http://schema.org/Rating"})

            starsfull= starsbase.findAll('i',{'class':"icon-star-full"})
            starshalf = starsbase.findAll('i',{'class':"icon-star-half"})
            total_stars = len(starsfull) + (len(starshalf)*.5)

            return reviewhtml.get_text(), float(total_stars)

    def dumpdoc(self, doctext, tofile):
        with open(tofile, mode="a") as f:
            f.write(str(doctext))
            f.seek(0)
            print("Review Saved.")
            f.close()

    def normalize(self, x):

        bins = [float(-1 + i*float(1/8)) for i in range(17)]
        review_score = float(0)
        while review_score == 0:
            for t in range(2, 17, 2):
                if float(x) >= bins[t-2] and float(x) < bins[t]:
                    review_score += t/4
                else:
                    pass
        return review_score


    def sentiment_score(self):
        
        apidict = {"mashape":{"apiurl":"https://alchemy.p.mashape.com/url/URLGetTextSentiment?",
                              "header":{"X-Mashape-Key":self.apikey, 
                                        "user-agent":'Chrome 40.0.2228.0', "accept":"text/plain"},
                              "payload":{"url":self.review_url, "outputMode":"json"}},
                   "alchemy":{"apiurl":'http://gateway-a.watsonplatform.net/calls/url/URLGetTextSentiment?',
                              "header":{'user-agent':'Chrome 40.0.2228.0', "accept":"text/plain"},
                              "payload":{"apikey":self.apikey,
                                         "url":self.review_url, "outputMode":"json"}}}
        
        
        apiargs = apidict[self.api]
        try:
            req = requests.get(apiargs["apiurl"], params=apiargs["payload"], headers=apiargs["header"])
    
        except Exception as errmsg:
            print("Err: %s" % errmsg)
        else:
            js = json.loads(req.text)
            try:
                rawscore = float(js["docSentiment"]["score"])
                review_sent = js["docSentiment"]["type"]
            except KeyError:
                print("API limit reached.")
            else:
                return review_sent, rawscore

    def compare(self, title, year, ID):
        
        try:
            htmldoc, obs = self.observed(title, year, ID)
        except Exception as err:
            return False
        else:
            if obs is False:
                return False
            else:
                self.dumpdoc(htmldoc, os.path.join(datadir, "reviews/%s.html" % title))
                             
                sentiment, sentscore = self.sentiment_score()
                measured = self.normalize(sentscore)
    
                diff = float(obs-measured)
                try:
                    pcterr = abs(diff)/measured
                except Exception as err:
                    pcterr = 0
                else:
                    
                    row = tuple([ID, title, year, obs, measured, diff, pcterr, sentiment, sentscore, self.review_url])
                    self.data.append(row)
                    return row
        
                    print('%s: \n Measured: %s (%s)\n Observed: %s\n Difference: %s\n Percent Error: %d ' % (title, str(measured),
                                                                                                         str(sentscore), str(observed),
                                                                                                         str(abs(float(diff)))))
                
    
    def _mktable(self):
        stmt = '''CREATE TABLE IF NOT EXISTS review_stars (id,
title TEXT, release_year TEXT,observed_stars REAL,measured_stars REAL,diff REAL,
perc_err REAL,sentiment TEXT, sentiment_score REAL,review_url TEXT)'''
        curs.execute(stmt)
        conn.commit()
        print("Table Created.")


    def _save2db(self, values):
        stmt = '''INSERT INTO review_stars(id, title, release_year, observed_stars,
measured_stars, diff, perc_err, sentiment, sentiment_score, review_url) VALUES (?,?,?,?,?,?,?,?,?,?)'''
        curs.execute(stmt, values)


    def pull_stored(self, fields, table):

        stmt = '''SELECT %s FROM %s''' % (",".join(fields), table)
        try:
       
            curs.execute(stmt)
        except Exception as err:
            print(err)
        else:
            rows = curs.fetchall()
            for row in rows:
                self.data.append(row)
            return self.data
        
     
    def _duptest(self, t):
        
        stmt = '''SELECT title from review_stars'''
        try:
            curs.execute(stmt)
        except:
            self._mktable()
            curs.execute(stmt)
            
            
        titles = [i[0] for i in curs.fetchall()]
        if t in titles:
            return True
        else:
            return False


    def get(self, fieldnames, dbtable, save=True):
        rows = self.pull_stored(fields=fieldnames, table=dbtable)

        for i in range(len(rows)):
            title = rows[i][1].replace("\xa0", "")
            ID = rows[i][0]
            year = rows[i][2]
            
            if self._duptest(title) is False:
                print("Working on %s (%s of %s)..." % (title, str(ID), str(len(rows))))
                try:
                    row = self.compare(title, year, ID)
                except Exception as err:
                    print(err)
                    pass
                else:
                    if row is False:
                        print("No review available")
                    else:
                        self.data.append(row)
                        if save is True:
                            print("Saving %s..." % title)
                            self._save2db(values=row)
                            print("Committing to db...")
                            conn.commit()
                        else:
                            self.data.append(row)
            else:
                print("Skipping %s. Already in database." % title)
                pass
         
        curs.close()
        conn.close()
        print("Done.")
        

    def __iter__(self):
        return self.data
    

class StatsTests(Ratings):
    
    def __init__(self, apiname="mashape"):
        Ratings.__init__(self, api=apiname)
        try:
            self.pull_stored(["title","observed_stars","measured_stars","diff"], "review_stars")
        except:
            self.get(["title","observed_stars","measured_stars","diff"], "review_stars")
            
            
    def BinomTest(self):
        freq = self.Frequencies()
            
        difflist = [i[3] for i in self.data]
        success = float(0)
        fails = float(0)
        for i in range(len(difflist)):
            if float(difflist[i]) == 0:
                success += 1
            else:
                fails += 1
                
                    
        binomtest = stats.binom_test(x=int(success), n=freq["Total_Count"])
        bin = stats.binom.stats(n=freq["Total_Count"], p=success/freq["Total_Count"], moments='mvsk')
        print("Mean=%s, Variance=%s, Skew=%s, Kurtosis=%s" % (bin[0], bin[1], bin[2], bin[3]))
        
        
    
    def Frequencies(self, counts=True, percents=True):

        measure = dict(Counter([i[2] for i in self.data]))
        observe = dict(Counter([i[1] for i in self.data]))
        diffs = dict(Counter([i[3] for i in self.data]))
        totalN = len([i[3] for i in self.data])
        freqdict = {"Total_Count":totalN}
        if percents is True:
            diff_pctfreq = dict(map(lambda x: (x, (diffs[x]/totalN)), 
                                    [k for k in diffs.keys()]))
            
            measure_pctfreq = dict(map(lambda x: (x, (measure[x]/totalN)), 
                                       [k for k in measure.keys()]))
            
            observe_pctfreq = dict(map(lambda x: (x, (observe[x]/totalN)), 
                                       [k for k in observe.keys()]))
                
  
            freqdict.update({"Differences_Perc":diff_pctfreq, 
                             "Measured_Perc":measure_pctfreq, 
                             "Observed_Perc":observe_pctfreq})
            
        else: pass
        
        if counts is True:
            freqdict.update({"Differences_Count":diffs, 
                             "Measured_Count":measure, 
                             "Observed_Count":observe})
        else: pass
        
        return freqdict
    
    
    def Correlation(self):
        degfree = self.Frequencies()["Total_Count"]-1
        obs_bins = self.Frequencies()['Observed_Count']
        exp_bins = self.Frequencies()['Measured_Count']
        
        arrObs = numpy.array([float(i[1]) for i in self.data])
        arrExp = numpy.array([float(j[2]) for j in self.data])

        rankcorr = stats.spearmanr(a=arrObs, b=arrExp)
        print(rankcorr)
        ## SpearmanrResult(correlation=0.51898744277333109, pvalue=2.1104149202665904e-129)

        
    def Plot(self, fmt, fields=None):

        if fmt == "Count":
            
            freqs = self.Frequencies(counts=True, percents=False)
            obslist = list(map(lambda x, y: (x, y, y+.35), [v for v in freqs["Observed_Count"].values()], [k for k in freqs["Observed_Count"].keys()]))
            measlist = list(map(lambda x, y: (x, y, y+.30), [v for v in freqs["Measured_Count"].values()], [k for k in freqs["Measured_Count"].keys()]))
            difflist = list(map(lambda x, y: (x, y, y+.25), [v for v in freqs["Differences_Count"].values()], [k for k in freqs["Differences_Count"].keys()])) 

            
        elif fmt == "Percent":   
            freqs = self.Frequencies(counts=False, percents=True)
            obslist = list(map(lambda x, y: (round(x*100, 2), y, y+.35), [v for v in freqs["Observed_Perc"].values()], [k for k in freqs["Observed_Perc"].keys()]))
            measlist = list(map(lambda x, y: (round(x*100, 2), y, y+.30), [v for v in freqs["Measured_Perc"].values()], [k for k in freqs["Measured_Perc"].keys()]))
            difflist = list(map(lambda x, y: (round(x*100, 2), y, y+.25), [v for v in freqs["Differences_Perc"].values()], [k for k in freqs["Differences_Perc"].keys()])) 
        
        histdata = {"Observed":obslist, "Measured":measlist, "Differences":difflist}
            
        

        hist = pygal.Histogram(y_title=fmt, x_title="Stars")
        hist.title = "Star Ratings Distribution"
        if fields is not None:
            for field in fields:
                hist.add(field, histdata[field])
        else:
            for field in list(histdata.keys()):
                hist.add(field, histdata[field])
            
        print("Plot URL: \n"), 
        hist.render_in_browser()

    



if __name__ == "__main__":
    
    stat = StatsTests()
    stat.Correlation()
    stat.BinomTest()
    
    stat.Plot("Percent", fields=["Observed", "Measured"])
    sleep(2)
    stat.Plot("Percent", fields=["Differences"])




