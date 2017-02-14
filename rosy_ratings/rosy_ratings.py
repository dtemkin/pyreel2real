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
from csv import DictWriter
import pandas
from math import sqrt


import plotly.plotly as pltly
import plotly.graph_objs as graphs
from plotly import figure_factory as figfactory
from plotly import tools


fullpath= lambda x: os.path.abspath(os.path.join(os.path.dirname(__file__), x))

printbreak="\n###########################################\n"

sqlfile = fullpath("main.db")
conn = sqlite3.connect(sqlfile)
curs = conn.cursor()


class Ratings:


    def __init__(self, api, apikey=None):
        self.review_url = None
        self.api = api
        self.apikey = apikey
        self.useragent = "Mozilla/5.0 (X11; Linux x86_64; rv:50.0) Gecko/20100101 Firefox/50.0"# REQUIRED-- Check out my github repo @ github.com/just-dantastic/useragent-hoodini
        self.rawscore, self.review_sent = None, None
        self.data = []


    def _format_title(self, x, y):
        title = re.sub('[%s]' % re.escape(string.punctuation), '', x.lower())

        urlref = str(title + " %s" % y).split()
        urlref = "-".join(urlref)
        return urlref

    def _build_url(self, url, **args):
        args = dict(**args)
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
        review_score = float(0)
        if x < float(-.7778):
            review_score += 0
        elif float(-.7778) <= x < float(-.5556):
            review_score += 0.5
        elif float(-.5556) <= x < float(-.3334):
            review_score += 1.0
        elif float(-.3334) <= x < float(-.1112):
            review_score += 1.5
        elif float(-.1112) <= x < float(.1110):
            review_score += 2.0
        elif float(.1110) <= x < float(.3332):
            review_score += 2.5
        elif float(.3332) <= x < float(.5554):
            review_score += 3.0
        elif float(.5554) <= x < float(.7776):
            review_score += 3.5
        elif x >= float(.7776):
            review_score += 4.0
        
        return review_score
        

    def sentiment_score(self):
        
        apidict = {"mashape":{"apiurl": "https://alchemy.p.mashape.com/url/URLGetTextSentiment?",
                              "header": {"X-Mashape-Key": self.apikey,
                                        "user-agent": 'Chrome 40.0.2228.0', "accept":"text/plain"},
                              "payload": {"url": self.review_url, "outputMode":"json"}},
                   "alchemy":{"apiurl": 'http://gateway-a.watsonplatform.net/calls/url/URLGetTextSentiment?',
                              "header": {'user-agent':'Chrome 40.0.2228.0', "accept":"text/plain"},
                              "payload": {"apikey":self.apikey, "url":self.review_url, "outputMode":"json"}}}
        
        
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
            htmldoc, observed = self.observed(title, year, ID)
        except Exception as err:
            return False
        else:
            if observed is False:
                return False
            else:
                self.dumpdoc(htmldoc, os.path.join(self.datadir, "reviews/%s.html" % title))
                             
                sentiment, sentscore = self.sentiment_score()
                measured = self.normalize(sentscore)

                diff = float(observed-measured)
                try:
                    pcterr = abs(diff)/measured
                except Exception as err:
                    pcterr = 0
                    pass
                else:
                    
                    row = {"id":ID, "title":title, "release_year":year, "observed_stars":observed,
                           "measured_stars":measured, "diff":diff, "perc_err":pcterr, 
                           "sentiment":sentiment, "sentiment_score":sentscore, 
                           "review_url":self.review_url}
                    self.data.append(tuple([r for r in row.values()]))
        
                    print("%s: \n Measured: %s (%s)\n Observed: %s\n Difference: %s\n Percent Error: %d " % (title, str(measured),
                                                                                                             str(sentscore), str(observed),
                                                                                                             str(abs(float(diff))), float(pcterr)))
                    return row


    def _mktable(self):
        stmt = """CREATE TABLE IF NOT EXISTS review_stars (id, title TEXT, release_year TEXT, observed_stars REAL,measured_stars REAL,diff REAL, perc_err REAL,sentiment TEXT, sentiment_score REAL,review_url TEXT)"""
        curs.execute(stmt)
        conn.commit()
        print("Table Created.")
    


    def save(self, dct, to_db=True, to_csv=True):
        if to_db is True:
            stmt = """INSERT INTO review_stars(id, title, release_year, observed_stars, measured_stars, diff, perc_err, sentiment, sentiment_score, review_url) VALUES (?,?,?,?,?,?,?,?,?,?)"""
            curs.execute(stmt, tuple([v for v in dct.values()]))
        if to_csv is True:
            filepath = fullpath("../review_stars.csv")
            header = ["id", "title", "release_year", "observed_stars",
                      "measured_stars", "diff", "perc_err", "sentiment", 
                      "sentiment_score", "review_url"]
            
            with open(filepath, mode="a") as f:
                writr = DictWriter(f, fieldnames=header)
                if os.path.isfile(filepath):
                    pass
                else:
                    writr.writeheader()
                    
                writr.writerow(dct)
                


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
        row_count = len(rows)
        for i in range(row_count):
            title = rows[i][1].replace("\xa0", "")
            ID = rows[i][0]
            year = rows[i][2]
            
            if self._duptest(title) is False:
                print("Working on %s (%s of %s)..." % (title, str(ID), str(row_count)))
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
                            self.save(dct=row)
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
    
    def sql2csv(self, sqltable, fields):
        data = self.pull_stored(sqltable, fields)
        csvfile = "../%s.csv" % sqltable
        with open(csvfile, mode="a") as f:
            writr = DictWriter(f, fieldnames=fields)
            if os.path.isfile(csvfile):
                writr.writeheader()
            else:
                pass
            
            for i in range(len(data)):
                writr.writerow(data[i])
            print("File %s Saved." % sqltable)
            f.close()

  
    
        

    def __iter__(self):
        return self.data
    

class StatsTests(Ratings):
    
    def __init__(self, apiname="mashape"):
        Ratings.__init__(self, api=apiname)
        try:
            self.pull_stored(["title","observed_stars","measured_stars","diff","sentiment_score"], "review_stars")
        except:
            self.get(["title","observed_stars","measured_stars","diff","sentiment_score"], "review_stars")
            

    def Frequencies(self, counts=True, percents=True):        
        measure = dict(Counter([i[2] for i in self.data]))
        observe = dict(Counter([i[1] for i in self.data]))
        diffs = dict(Counter([i[3] for i in self.data]))
        totalN = len([i[3] for i in self.data])
        measure.update({4.0:0, 0.0:0})
               
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

    def ContingencyTable(self):
        vals = []
        for i in self.data:
            vals.append((i[1], i[2]))


        totals = dict(Counter([x[0] for x in vals]))
        totals.update({0.0:0, 4.0:0})
        counts = {}
        for k in totals.keys():
            counts.update({k: dict(Counter(sorted([x[1] for x in vals if x[0] == k])))})
            counts[k].update({0.0:0, 4.0:0})


        counts_df = pandas.DataFrame.from_dict(counts).fillna(0)
        counts_df.insert(9, "total", [sum(counts_df.loc[x,]) for x in counts_df.index])
        counts_df.loc["total"] = counts_df.sum()
        counts_df.index = ["".join(["m",str(i)]) for i in counts_df.index]
        counts_df.columns = ["".join(["o", str(j)]) for j in counts_df.columns]



        return counts_df.loc[["m0.5","m1.0","m1.5",
                              "m2.0","m2.5","m3.0"],
                             ["o0.5","o1.0","o1.5",
                              "o2.0","o2.5","o3.0",
                              "o3.5","o4.0"]]

    def ChiSquared(self):
        Vs = []
        probs = self.ContingencyTable()
        subtotals = list(map(lambda x: sum(x), [probs[p] for p in probs.columns]))
        totalobs = sum(subtotals)
        nrows = len(probs.index)
        ncols = len(probs.columns)

        chisq, pval0, ddof, exp = stats.chi2_contingency(probs)
        chisq_array, pval = stats.chisquare(probs, exp)


        for x in range(len(chisq_array)):
            v = sqrt(chisq_array[x]/(subtotals[x]*min(nrows-1, ncols-1)))
            Vs.append(v)
        totalV = sqrt(chisq/(totalobs*min(nrows-1, ncols-1)))
        print("ChiSquared Analysis with Cramers V",
              printbreak,
              "Contingency Table\n", probs,
              "\ndf\n", ddof,
              "\np-value\n", pval0,
              "\nExpected Values\n", exp,
              "\nX2\n", chisq_array,
              "\np-value\n", pval,
              printbreak,
              "\nCramers V\n",
              "Overall: ", totalV,
              "\nBy Group: ", Vs)

    def Correlation(self):

        rankcorr = stats.spearmanr(a = numpy.array([float(i[1]) for i in self.data]),
                                   b = numpy.array([float(j[2]) for j in self.data]))
        print(printbreak,
              "\nCorrelation: ",
              rankcorr)


    def Plot(self):
        freqs = self.Frequencies(counts=True, percents=True)
        df = pandas.DataFrame({"title":[x[0] for x in self.data],
                               "observed stars":[x[1] for x in self.data],
                               "sentiment score":[x[4] for x in self.data]})

        group_stats = {}

        groupby_data = df.groupby(["observed stars"])

        for group in [0.0,0.5,1.0,1.5,2.0,2.5,3.0,3.5,4.0]:
            group_data = groupby_data.get_group(group)["sentiment score"]

            mdn = numpy.median(group_data)
            group_stats[group] = mdn


        box0 = dict(type="box", y=[x[2] for x in self.data], boxmean="sd",
                    name="Measured Stars",marker={"color":"#9d87ed"},xaxis="x1",yaxis="y2")
        box1 = dict(type="box", y=df["observed stars"], boxmean="sd",
                    name="Observed Stars",marker={"color":"#87aaed"}, xaxis="x1",yaxis="y2")

        obsbars = dict(type="bar", x=[k for k in freqs["Observed_Perc"].keys()],
                       y=[v for v in freqs["Observed_Perc"].values()],
                       name='Observed Star Ratings',
                       xaxis="x2", yaxis="y1",marker={"color":"#87aaed"})
        measbars = dict(type="bar", x=[k for k in freqs["Measured_Perc"].keys()],
                        y=[v for v in freqs["Measured_Perc"].values()],
                        name='Measured Star Ratings', xaxis="x1", yaxis="y1",
                        marker={"color":"#9d87ed"})

        diffs = dict(Counter(list(map(lambda x, y: x-y,
                                      [float(i[1]) for i in self.data],
                                      [float(j[2]) for j in self.data]))))


        diffbars = graphs.Bar(x=[x for x in diffs.keys()],
                              y=[y for y in diffs.values()],
                              marker=dict(color="#ed8787"))


        fig = tools.make_subplots(rows=4, cols=2,
                                  specs=[[{}, {'rowspan': 2}],
                                         [{}, None],
                                         [{'rowspan': 2, 'colspan': 2}, None],
                                         [None, None]], print_grid=False,
                                  subplot_titles=('Measured Star Rating Groups',
                                                  'Measured & Observed Stars Box Plot with Median',
                                                  'Observed Star Rating Groups',
                                                  'Difference Counts (Measured - Observed)'))


        fig.append_trace(obsbars, 1, 1)
        fig.append_trace(measbars, 2, 1)
        fig.append_trace(box0, 1, 2)
        fig.append_trace(box1, 1, 2)
        fig.append_trace(diffbars, 3, 1)
        fig["layout"].update(showlegend=False, title="Observed v Measured Stars")
        violin = figfactory.create_violin(df, data_header="sentiment score",
                                          group_header="observed stars",
                                          height=500, width=800,
                                          group_stats=group_stats,
                                          use_colorscale=True,
                                          title="Sentiment Score to Observed Stars")


      
        # pltly.plot(fig)
        # sleep(2)
        pltly.plot(violin)




stat = StatsTests()

stat.ChiSquared()
stat.Correlation()

stat.Plot()

