import sqlite3
from data import imdb, omdb, factory
from utils import fullpath
import os
from useragentx.useragent import spoof
import csv
import re
from datetime import datetime
from data import reviews as rev



class Data(object):
    def __init__(self, mediatype, dbfile=fullpath("data/data.db")):
        self.mediatype = mediatype
        self.req_headers = {'user-agent': spoof().browser("Firefox", 0)}
        self.dbfile = dbfile
        self.db = Database(dbfile=self.dbfile)
        self.movies = []

    def collect(self, args, addtl_items=list()):

        for a in range(len(args)):
            movie = factory.Movie().__dict__
            title, year = args[a]["title"], args[a]["year"]
            try:
                print("Checking %s" % title)
                if self.db.check(title, year) is False:
                    metadata = omdb.Lookup(media=self.mediatype, by="title", title=title, year=year)
                movie.update(self._format_data(metadata_obj=metadata()))

            except Exception:
                print("Skipping %s" % title)
                pass
            else:
                print("Adding %s" % title)
                if "oscars" in addtl_items:
                    oscars = imdb.Awards(ID=movie["imdbID"])
                    movie.update(oscars())
                if "boxoffice" in addtl_items:
                    boxoffice = imdb.BoxOffice(ID=movie["imdbID"])
                    movie.update(boxoffice())
                if "review" in addtl_items:
                    review = rev.RogerEbert(title=movie["title"], year=movie["release_year"])

                    if a >= 950:
                        movie.update(self.review_data(api=rev.Sentiment(apiname="alchemyapi",
                                                                        apikey="P2xDP6WmqaIBVMfEIRlG2lJG1h_AQ2YVAPvPZcYKhHKh",
                                                                        review_url=review.url), review=review))
                    else:
                        movie.update(self.review_data(api=rev.Sentiment(apiname="mashape",
                                                                        apikey="Y38nfdAaj6mshBnxcchWlqZHg66xp1aELvsjsnPrNbYplNBYk5",
                                                                        review_url=review.url), review=review))

                movie.update({"watched": args[a]["watched"]})
                movie.pop("_dict")
                self.movies.append(movie)

    def review_data(self, api, review):
        return {
            "star_rating": review.star_rating(), "review_sentiment": api.__str__(), "review_text": review.review_text(),
            "sentiment_score": api.score()
        }

    def _format_data(self, metadata_obj):
        patt_one = re.compile("\(.*?\)")
        data = {}
        data.update({
                        "title": metadata_obj["Title"], "release_year": metadata_obj["Year"],
                        "genres": metadata_obj["Genre"].replace(", ", "|"),
                        "writers": re.sub(patt_one, "", metadata_obj["Writer"]).replace(", ", "|"),
                        "directors": re.sub(patt_one, "", metadata_obj["Director"]).replace(", ", "|"),
                        "actors": metadata_obj["Actors"].replace(", ", "|"),
                        "runtime": metadata_obj["Runtime"].replace("Min", ""),
                        "langs": metadata_obj["Language"].replace(", ", "|"),
                        "plot": metadata_obj["Plot"], "mpaa_rating": metadata_obj["Rated"],
                        "countries": metadata_obj["Country"].replace(", ", "|"),
                        "prodco": metadata_obj["Production"].replace("/", "|"),
                        "poster_url": metadata_obj["Poster"], "imdbID": metadata_obj["imdbID"]
                    })

        if metadata_obj["DVD"] == "N/A":
            data.update({"dvd_release": "NULL"})
        else:
            data.update({"dvd_release": datetime.strptime(metadata_obj["DVD"], "%d %b %Y").strftime("%Y-%m-%d")})
        if metadata_obj["imdbVotes"] == "N/A":
            data.update({"imdbVotes": "0"})
        else:
            data.update({"imdbVotes": str(metadata_obj["imdbVotes"].replace(",", ""))})

        if metadata_obj["Released"] == "N/A":
            data.update({"release_date": "NULL"})
        else:
            data.update({"release_date": datetime.strptime(metadata_obj["Released"], "%d %b %Y").strftime("%Y-%m-%d")})
        if metadata_obj["BoxOffice"] == "N/A":
            data.update({"boxoffice_todate": "0"})
        else:
            data.update({"boxoffice_todate": str(metadata_obj["BoxOffice"].replace("$", "").replace(",", ""))})
        if metadata_obj["imdbRating"] == "N/A":
            data.update({"imdbRating": "0"})
        else:
            data.update({"imdbRating": metadata_obj["imdbRating"]})

        return data

    def titles_list(self, loc=fullpath("data/movies.txt"), assume_watched=False):
        vals = []
        if os.path.isfile(fullpath(loc)):
            with open(fullpath(loc), mode="r") as f:
                readr = csv.DictReader(f, delimiter="\t", fieldnames=["title", "year", "rank", "watched"])
                next(readr)
                for row in readr:
                    vals.append(row)
        elif os.path.isdir(fullpath(loc)):


            ddir = os.walk(fullpath(loc))
            files = next(ddir)[2]
            for f in files:
                name, ext = os.path.splitext(f)
                if ext in [".mkv", ".mp4", ".avi", ".divx", ".mov", ".mpg", ".mpeg"]:
                    d = {}
                    if name.find(")") > -1:
                        ttl, yr = name.split("(")
                        yr = yr.replace(")", "")

                    else:
                        ttl, yr = name, ""
                    if assume_watched is False:
                        d.update({"title": ttl, "year": yr, "rank": -1, "watched": None})
                    else:
                        d.update({"title": ttl, "year": yr, "rank": -1, "watched": 1})
                    vals.append(d)
                else:
                    pass


        else:
            raise ValueError("Cannot render titles list from loc")
        return vals




class Database(object):
    def __init__(self, dbfile):
        self.dbfile = dbfile
        self.conn = sqlite3.connect(dbfile)
        self.conn.row_factory = sqlite3.Row
        self.curs = self.conn.cursor()

    def make_table(self, table, fields):
        fieldsx = []

        if type(fields[0]) is tuple:
            for i in fields:
                fmted = " ".join(i)
                fieldsx.append(fmted)
        else:
            fieldsx = fields

        mktable = """create table if not exists %s (%s)""" % (table, ", ".join(fieldsx))
        self.curs.execute(mktable)
        self.conn.commit()

    def select(self, table="main", fields="all", nresults="all", **filters):

        exts = []
        for item in dict(filters).items():
            exts.append(" %s==%s " % (item[0], item[1]))

        if fields == "all":
            base_stmt = """select * from %s""" % table
        else:
            base_stmt = """select %s from %s""" % (", ".join(fields), table)

        if len(exts) > 0:
            extt = " and ".join(exts)
            stmt = " ".join([base_stmt, " where ", extt])
        else:
            stmt = base_stmt

        self.curs.execute(stmt)
        if nresults == "all":
            results = self.curs.fetchall()
        else:
            results = self.curs.fetchmany(size=int(nresults))
        return results

    def check(self, title, year):
        try:
            stmt = """select * from main where title==%s""" % (title)
            self.curs.execute(stmt)
            existing = self.curs.fetchall()
        except:
            return False
        else:
            if len(existing) > 0:
                try:
                    stmt0 = """select * from main where title==%s and release_year==%s""" % (title, year)
                    self.curs.execute(stmt0)
                except:
                    return True
                else:
                    self.curs.execute(stmt0)
                    existing0 = self.curs.fetchall()
                    if len(existing0) > 0:
                        return True
                    else:
                        return False
            else:
                return False

    def update(self, row, table="main", **kwargs):
        skip_dupes = kwargs.get("skip_duplicates", True)

        if type(row) is list:
            valid_rows = []
            if len(row) == 0:
                pass
            else:
                if skip_dupes is True:
                    for r in row:
                        if self.check(r["title"], r["release_year"]) is False:
                            print(r["title"], "-- adding to database")
                            valid_rows.append(r)
                        else:
                            print(r["title"], "-- already in database")
                            pass
                else:
                    print(row["title"], "-- adding to database")
                    valid_rows.extend(row)
                value_marks = ["?"] * len([r for r in valid_rows[0].values()])
                stmt = "insert into %s values (%s)" % (table, ", ".join(value_marks))
                self.curs.executemany(stmt, valid_rows)

        else:
            if skip_dupes is True:
                if self.check(row["title"], row["release_year"]) is False:
                    value_marks = ["?"] * len([r for r in row.values()])
                    stmt = "insert into %s values (%s)" % (table, ", ".join(value_marks))
                    self.curs.execute(stmt, tuple([v for v in row.values()]))

                else:
                    pass
            else:
                value_marks = ["?"] * len([r for r in row.values()])
                stmt = "insert into %s values (%s)" % (table, ", ".join(value_marks))
                self.curs.execute(stmt, tuple([v for v in row.values()]))

            self.conn.commit()

    def build(self, rows, table="main"):
        self.make_table(table=table, fields=[k for k in rows[0].keys()])
        self.update(row=rows, table=table)

    def close(self):
        self.curs.close()

        self.conn.commit()
        self.conn.close()
