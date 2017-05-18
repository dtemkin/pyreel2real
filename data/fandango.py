import requests
from bs4 import BeautifulSoup as bsoup
from useragentx.useragent import spoof
import re
import numpy as np
from datetime import datetime
import data
import requests_cache
from utils import fullpath
from pandas import DataFrame

class Theater(object):

    def __init__(self):

        self.url = "http://www.fandango.com/moviesintheaters"

    def listings(self):


        req = requests.get(self.url, headers={"user-agent":spoof().browser("Chrome", 0)})
        soup = bsoup(req.text, "html5lib")
        titles = soup.findAll("a",{"class":"visual-title dark"})

        ttls = np.unique([title.get_text().strip() for title in titles])

        dicts = []
        patt = re.compile("..\dth\s(Anniversary)")
        for t in ttls:

            if t.find("3D") > -1:
                pass
            elif t.find("Anniversary") > -1:
                pass
            elif t.find("(") > -1:
                ttl, yr = t.split(" (")
                dicts.append({"title": ttl, "year": yr.replace(")", ""), "rank": "","watched":None})
            else:
                ttl, yr = t, ""
                dicts.append({"title": ttl, "year": yr, "rank": "", "watched":None})

        m = data.Data(mediatype="movie")
        m.collect(args=dicts)
        return m.movies

    def save(self, data, file=fullpath("data/fandango.ls")):
        with open(file, mode="w") as f:
            df = DataFrame(data)
            df.to_csv(f)
        f.close()
