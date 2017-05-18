from abc import ABCMeta
from useragentx.useragent import spoof
import requests
from bs4 import BeautifulSoup as bsoup
import re

class Base(metaclass=ABCMeta):

    def __init__(self, ID):
        self.url = 'http://www.imdb.com/title/%s' % ID
        self.headers = {"user-agent":spoof().browser("Chrome", 0)}

    def _parser(self, rawhtml, parser_lib):
        raise NotImplementedError("Failed to implement html parser")

class BoxOffice(Base):


    def __init__(self, ID, **kwargs):
        super().__init__(ID=ID)

    def _parser(self, rawhtml, parser_lib):
        soup = bsoup(rawhtml, parser_lib)
        mainblok = soup.find("div", {"class":"article", "id":"titleDetails"})

        subbloks = mainblok.findAll("h4",{"class":"inline"})
        pattrn = re.compile('\(.*?\)')
        data = {"gross":0., "opening_weekend":0., "budget":0.}
        for blk in subbloks:
            heading = blk.get_text().replace(":","").replace(" ","_").lower()
            if heading in ["opening_weekend","gross","budget"]:
                txt = blk.next_element.next_element
                txt = txt.strip().replace(",","")
                if txt.find("$") > -1:
                    val = re.sub(pattrn, "", txt.replace("$",""))
                else:
                    val = 0
                data[heading.lower()] += float(val)
            else:
                pass

        return self.add_calc_fields(data)

    def add_calc_fields(self, vals_dict):
        vals = vals_dict
        if vals_dict["gross"] == float(0):
            pct_of_gross = 0.
        else:
            pct_of_gross = float(vals_dict["opening_weekend"])/float(vals_dict["gross"])

        net_income = float(vals_dict["gross"]) - float(vals_dict["budget"])
        vals.update({"pct_of_gross": str(pct_of_gross), "net_income": str(net_income)})
        return vals

    def __call__(self, *args, **kwargs):
        parserlib = kwargs.get("parser_lib", "html5lib")
        url = '/'.join([self.url, '?ref_=fn_al_tt_1'])
        req = requests.get(url, headers=self.headers)
        data = self._parser(req.text, parser_lib=parserlib)
        return data

class Awards(Base):

    def __init__(self, ID, **kwargs):
        super().__init__(ID=ID)

    def _parser(self, rawhtml, parser_lib, awardtypes=["oscar"]):
        soup = bsoup(rawhtml, parser_lib)
        mainblok = soup.find("div", {"id": "main"})
        subbloks = mainblok.findAll("table", {"class":"awards"})
        data = {}
        for i in awardtypes:
            data.update({"%s_won" % i:0, "%s_nominated" % i:0})
        for blk in subbloks:
            bodies = blk.findAll("tbody")
            for body in bodies:
                outcomes = body.findAll("td", {"class":"title_award_outcome"})
                cats = body.findAll("span", {"class":"award_category"})
                for i in range(len(cats)):
                    if cats[i].get_text().lower() in awardtypes:
                        data["oscar_%s" % (outcomes[i].find("b").get_text().lower())] += int(outcomes[i].attrs["rowspan"])
                    else:
                        pass
        return data


    def __call__(self, *args, **kwargs):
        awardss = kwargs.get("awardtypes", None)
        parserlib = kwargs.get("parser_lib", "html5lib")
        url = '/'.join([self.url, 'awards?ref_=tt_awd'])

        req = requests.get(url, headers=self.headers)
        if awardss is None:
            data = self._parser(req.text, parser_lib=parserlib)
        else:
            data = self._parser(req.text, parser_lib=parserlib, awardtypes=[awardss])

        return data