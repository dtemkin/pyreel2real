import re
import string
import requests
from useragentx.useragent import spoof
from bs4 import BeautifulSoup as bsoup
from utils import fullpath

class RogerEbert(object):

    def __init__(self, title, year):
        self.title, self.year = title, year
        self.header = {"user-agent": spoof().browser("Chrome", 0)}
        self.baseurl = "http://www.rogerebert.com/reviews/"
        self.url = self._build_url()

    def _format_title(self, x, y):
        title = re.sub('[%s]' % re.escape(string.punctuation), '', x.lower())

        urlref = str(title + " %s" % y).split()
        urlref = "-".join(urlref)
        return urlref

    def _build_url(self):
        urlext = self._format_title(self.title, self.year)
        return "".join([self.baseurl, urlext])

    def _proc_request(self):
        try:
            req = requests.get(self.url, headers=self.header)
        except Exception as errmsg:
            print("Err: %s" % errmsg)
            return False
        else:
            soup = bsoup(req.text, 'html5lib')
            return soup

    def _clean_text(self, txt):
        patt = "\..*? }\);"
        re.compile(patt)
        re.sub(patt, "", txt)

    def review_text(self):
        soup = self._proc_request()
        if soup is False:
            review = ""
        else:
            try:
                reviewhtml = soup.find("div", {"itemprop": "reviewBody"})
                review = reviewhtml.get_text(strip=True)
            except AttributeError:
                review= ""

        return review

    def star_rating(self):
        soup = self._proc_request()
        if soup is False:
            rating = -1
        else:
            try:
                article = soup.find("article", {"class": "pad entry"})
                rating_items = article.find("span",{"itemprop": "reviewRating", "itemtype": "http://schema.org/Rating"})
            except AttributeError:
                rating = -1
            else:
                rating = float(rating_items.find("meta").attrs["content"])
        return rating

class Sentiment(object):

    def __init__(self, apiname, review_url, apikey):
        self.apidict = {
            "mashape": {"url": "https://alchemy.p.mashape.com/url/URLGetTextSentiment?",
                        "header": {"X-Mashape-Key": apikey, "user-agent": 'Chrome 40.0.2228.0', "accept": "text/plain"},
                        "payload": {"url": review_url, "outputMode": "json"}},
            "alchemyapi": {"url": 'http://gateway-a.watsonplatform.net/calls/url/URLGetTextSentiment?',
                           "header": {'user-agent': 'Chrome 40.0.2228.0', "accept": "text/plain"},
                           "payload": {"apikey": apikey, "url": review_url, "outputMode": "json"}}}

        if apiname.lower() in ["mashape","alchemyapi"]:
            self.api = self.apidict[apiname]
        else:
            print("Error: Invalid API")

    def _proc(self):
        try:
            req = requests.get(self.api["url"], params=self.api["payload"], headers=self.api["header"])
        except Exception as err:
            print("Err: %s" % err)
        else:
            return req

    def score(self):
        try:
            s = self._proc().json()
            s = s["docSentiment"]["score"]
        except Exception:
            return "None"
        else:
            return float(s)


    def __str__(self):
        try:
            s = self._proc().json()
            s = s["docSentiment"]["type"]
        except Exception:
            return "None"
        else:
            return s