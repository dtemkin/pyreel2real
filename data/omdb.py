import requests
from useragentx.useragent import spoof
from bs4 import BeautifulSoup as bsoup 


class API(object):

    def __init__(self, media, year):
        self.baseurl = "http://www.omdbapi.com/?"
        self.headers = {"user-agent":spoof().browser("Chrome", 0)}
        if media not in ["movie","episode","series"]:
            raise ValueError("invalid mediatype %s" % media)
        else:
            self.payload = {"type":media, "v": 1, "r": "json", 
                            "y": year}


class Lookup(API):

    def __init__(self, media, by, **kwargs):
        year = kwargs.get("year", "")

        super().__init__(media=media, year=year)
        filt = kwargs.get(by, None)
        if by.lower() == "title":
            if filt is None:
                raise ValueError("%s must be specfied if by=%s" % (by, by))
            else:

                self.payload.update({"t": filt})

        elif by.lower() == "id":
            if filt is None:
                raise ValueError("%s must be specfied if by=%s" % (by, by))
            else:
                self.payload.update({"i": filt})
        else:
            raise ValueError("invalid filter control by=%s" % by)

    def __call__(self):
        req = requests.get(self.baseurl, params=self.payload, headers=self.headers)
        raw = req.json()
        return raw

        
class Search(API):

    def __init__(self, media, title, **kwargs):
        yr = kwargs.get("year", "")
        super().__init__(media=media, year=yr)
        self.payload.update({"s":title})

    def __call__(self, **kwargs):
        self.payload.update({"page": kwargs.get("page", 1)})
        req = requests.get(self.baseurl, params=self.payload, headers=self.headers)
        raw = req.json()
        return raw




