from requests import get as reqget
from bs4 import BeautifulSoup as bsoup
from json import loads as jsloads
from useragent import platform


ua = platform().browser('Chrome', 0)
baseurl = 'https://www.youtube.com/results?search_query='


def _find_video_url(**args):
    args = dict(**args)
    url = ''.join([baseurl, '%s+%s+original+trailer' % (args['year'], args['movie_title'].lower().replace(' ','+'))])
    try:
        req = reqget(url, headers={'user-agent':ua})
    except:
        return 0, 0
    else:
        soup = bsoup(req.text, 'html5lib')

        x = soup.find('a', {'class':"yt-uix-sessionlink yt-uix-tile-link yt-ui-ellipsis yt-ui-ellipsis-2 spf-link "})
        d = soup.find("ul", {"class":"yt-lockup-meta-info"})
        views = d.li.nextSibling

        utube_id = x.attrs['href'][9:]
        vidurl = 'https://www.youtube.com/watch?v=%s' % utube_id
        if views is None:
            print("Oops Something Went Wrong! Skipping...")
            return 0, 'N/A'
        else:
            return views.string, vidurl
    


def get_user_votes(movie_title, year):
    
    nviews, url = _find_video_url(year=year, movie_title=movie_title)
    if url == 'N/A':
        print("No Youtube Trailer Found.")
        datadict = {'youtube_url':'N/A','trailer_nviews':0,'trailer_upvotes':0,
                    'trailer_uppct':0,'trailer_dnvotes':0,'trailer_dnpct':0}
        return datadict
    else:
        try:
            req = reqget(url, {'user-agent':ua})
        except:
            print("No Youtube Trailer Found.")
            datadict = {'youtube_url':'N/A','trailer_nviews':0,'trailer_upvotes':0,
                        'trailer_uppct':0,'trailer_dnvotes':0,'trailer_dnpct':0}
            return datadict
        else:
            soup = bsoup(req.text, 'html5lib')

            thumbup = soup.find('button', {'title':'I like this'})
            upvotes = thumbup.find('span', {"class":"yt-uix-button-content"})
            thumbdn = soup.find('button', {'title':'I dislike this'})
            dnvotes = thumbdn.find('span', {"class":"yt-uix-button-content"})
            nviews = nviews.replace(' views', '')

            numviews = int(nviews.replace(',', ''))
            try:
                upvotes = float(upvotes.string.replace(',',''))
            except:
                upvotes, dnvotes, totalvotes, uppct, dnpct = 0, 0, 0, 0, 0
            else:
                dnvotes = float(dnvotes.string.replace(',',''))
                totalvotes = upvotes + dnvotes
                if totalvotes == 0:
                    dnvotes, upvotes, totalvotes, uppct, dnpct = 0, 0, 0, 0, 0 
                else:
                    uppct = float(upvotes/totalvotes)
                    dnpct = float(dnvotes/totalvotes)

            datadict = {'youtube_url':url, 'trailer_nviews':int(numviews), 'trailer_upvotes':int(upvotes),
                        'trailer_uppct':float(uppct),'trailer_dnvotes':int(dnvotes), 'trailer_dnpct':float(dnpct)}

            movie_title = movie_title.replace('\n','')
            movie_title = movie_title.replace('\xa0','')
            print("Got Youtube Data for %s" % (movie_title))

            return dict(datadict)
