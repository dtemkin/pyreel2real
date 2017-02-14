from requests import get as reqget
from bs4 import BeautifulSoup as bsoup
from json import loads as jsloads
from useragent import platform

from datetime import datetime as dt

plat = platform()
ua = plat.browser("Chrome", 0)

class moviedata:
    
    def __init__(self, srcid, release_year):
        self.srcid = srcid
        self.apiurl = 'http://www.omdbapi.com/?'
        self.apiparams = {'i':srcid, 'type':'movie', 'y':release_year,
                          'plot':'full','r':'json'}
        self.baseurl = 'http://www.imdb.com/title'
        self.xtra_urlreq = None
        self.xtraurl = '/'.join([self.baseurl, self.srcid, '?ref_=fn_al_tt_1'])

    def _cleanstr(self, string):
        s = string.replace('\n', '')
        s = s.replace('$','')
        s = s.replace(',','')
        s = s.replace(' ','')
        s = s.replace('(USA)','')
        s = s.replace('(estimated)','')
        s = s.replace('(','')
        try:
            f = float(s)
        except ValueError:
            return float(0)
        else:
            return f

    def _production(self):
        data = []
        if self.xtra_urlreq is None:
            self.xtra_urlreq = reqget(self.xtraurl, headers={'user-agent':ua})
        else:
            try:
                soup = bsoup(self.xtra_urlreq.text, 'html5lib')
                orgs = soup.findAll('span',{'itemprop':'creator','itemscope':'','itemtype':'http://schema.org/Organization'})
            except:
                print("Oops Parser Problems, Skipping...")
                data.append('N/A')
            else:
                for org in orgs:
                    coname = org.find('span',{'class':'itemprop','itemprop':'name'})
                    data.append(coname.string)
            return {'prodco':'|'.join(data)}
    
    def _boxoffice(self):
        boxoffice_data = {'budget':None,'opn_wkend':None, 'gross':None, 'opn_pct_gross':None,'profit':None}
        if self.xtra_urlreq is None:
            self.xtra_urlreq = reqget(self.xtraurl, headers={'user-agent':ua})
        else:
            try:
                soup = bsoup(self.xtra_urlreq.text, 'html5lib')
                content = soup.findAll("h4",{"class":"inline"})
            except:
                print("Parsing Error")
                pass
            else:
                for target in content:
                    if target.string == 'Budget:':
                        budget = target.nextSibling
                        boxoffice_data['budget'] = self._cleanstr(budget)
                    elif target.string == 'Opening Weekend:':
                        opnwkend = target.nextSibling
                        if '(US)' in opnwkend:
                            boxoffice_data['opn_wkend'] = self._cleanstr(opnwkend)
                        else:
                            boxoffice_data['opn_wkend'] = None
                    elif target.string == 'Gross:':
                        gross = target.nextSibling
                        boxoffice_data['gross'] = self._cleanstr(gross)
                    else:
                        pass
        if boxoffice_data['gross'] > 0 and boxoffice_data['opn_wkend'] != None: 
            try:
                opnpct = round(float(boxoffice_data['opn_wkend']/boxoffice_data['gross']), 4)
            except TypeError or ValueError:
                boxoffice_data['opn_pct_gross'] = None
            else:
                boxoffice_data["opn_pct_gross"] = opnpct
        else:
            pass

        if boxoffice_data['budget'] is not None:
            try:
                netearn = float(boxoffice_data['gross']) - float(boxoffice_data['budget'])
            except TypeError or ValueError:
                boxoffice_data['profit'] = None
            else:
                boxoffice_data['profit'] = netearn
        else:
            pass
        
        return dict(boxoffice_data)

    def _awards(self):
        url = '/'.join([self.baseurl, self.srcid, 'awards?ref_=tt_awd'])
        urlreq = reqget(url, params=self.apiparams, headers={'user-agent':ua})

        soup = bsoup(urlreq.text, 'html5lib')
        main = soup.find('div',{'id':'main'})

        award_year = main.find("a",{"class":"event_year"})
        award_type = award_year.previousSibling
        if award_type.strip() == 'Academy Awards, USA':
            
            content = soup.find("table",{"class":"awards","cellpadding":'5','cellspacing':'0'})
            awards_ = content.findAll("td",{"class":"title_award_outcome"})

            for award in awards_:
                outcome = award.b.string
                if outcome == 'Won':
                    wins = award.attrs['rowspan']
                elif outcome == "Nominated":
                    noms = award.attrs['rowspan']
                else:
                    print('None Found')
            return {'award_year':str(award_year.string).strip(),'oscar_wins':int(wins), 'oscar_noms':int(noms)}
        else:
            return {'award_year':'N/A','oscar_wins':0,'oscar_noms':0}
 
    def get(self):
        apireq = reqget(self.apiurl, params=self.apiparams, headers={'user-agent':ua})
        d = jsloads(apireq.text, encoding='utf-8')
        prd = self._production()

        datadict = {'langs':'|'.join(d["Language"].split(', ')),
                    'countries':'|'.join(d['Country'].split(', ')),
                    'duration':int(d['Runtime'].replace(' min', '')),
                    'actors':'|'.join(d['Actors'].replace(' (characters)', '').split(', ')),
                    'writers':'|'.join(d['Writer'].split(', ')),
                    'directors':'|'.join(d['Director'].split(', ')),
                    'imdb_votes':int(d['imdbVotes'].replace(',','')),
                    'imdb_score':float(d['imdbRating']),
                    'mpaa_rating':d['Rated'],
                    'release_date':dt.strptime(d['Released'], "%d %b %Y").strftime("%Y%m%d"),
                    'metascore':d['Metascore'],'poster_url':d["Poster"]}
        
        datadict.update(self._production())

        datadict.update(self._boxoffice())
        datadict.update(self._awards())

        print("Got IMDB Data for %s" % d['Title'])
        return datadict


