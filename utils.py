'''
Created on Jan 9, 2017

@author: dysmas
'''
import os
import sqlite3


def fullpath(filename):
    return os.path.abspath(os.path.join(os.path.dirname(__file__), filename))


class database(object):
    
    def __init__(self, dbfile, autoconnect=True):
        self.dbfile = fullpath(dbfile)
        if autoconnect is True:
            try:
                self.conn, self.curs = self.connect(dbfile)
            except:
                print("Auto-Connect Fail.")
        else:
            pass
               
            
    
    def connect(self, db, mkCursor=True):
        conn = sqlite3.connect(dbfile=db)
        if mkCursor is True:
            return conn, conn.cursor()
        else:
            return conn


    def columns(self, tablename):
        
        tables = {"main":['id',"mediatype",'actors','directors',
                          'writers','release_year','release_date',
                          'prodco','countries','mpaa_rating',
                          'duration','imdb_id','title','genres',
                          'youtube_url','imdb_url','actor0','actor1',
                          'actor2','poster_url','facecnt_in_poster',
                          'langs','plot_kwds'],
                  "social":['actor0_fblikes','actor1_fblikes','actor2_fblikes',
                            'director_fblikes','cast_fblikes','movie_fblikes',
                            'imdb_score','imdb_votes','metascore','ncritic_reviews',
                            'nuser_reviews','trailer_nviews','trailer_upvotes',
                            'trailer_dnvotes','trailer_uppct','trailer_dnpct'],
                  "perform":['gross','budget','profit','opn_wkend','opn_pct_gross',
                             'award_year','oscar_wins','oscar_noms','pctile_bins'],
                  "rank":["title","rank","score"],
                  "reviews":["id","title","release_year","review_url",
                             "observed_stars","review_sentiment",
                             "sentiment_score","measured_stars",
                             "diff","pcterr","prob_measured"]}
        
        return tables[tablename]
    
    def mktable(self, tablename):
        if self.curs is None:
            self.curs = self.conn.cursor()
        else:
            pass
        
        t = columns[tablename]
        stmt = """CREATE TABLE IF NOT EXISTS %s(%s);""" % (name, ",".join(t))
        try:
            self.curs.execute(stmt)
        except Exception as err:
            print(err)
            return False
        else:
            self.curs.commit()
            return True
    
    
    def insert(tablename, row):
        if self.curs is None:
            self.curs = self.conn.cursor()
        else:
            pass
        
            
        self.mktable(tablename)
        valholders = ",".join([range("?"*len(row))])
        stmt = '''INSERT INTO %s VALUES (%s);''' % tablename, valholders
        try:
            self.curs.execute(stmt)
        except Exception as err:
            print(err)
            return False
        else:
            self.curs.commit()
            return True
        
    
    
    def simple_select(self, tablename, columns, nrows="all"):
        if self.curs is None:
            self.curs = self.conn.cursor()
        else:
            pass
        
        stmt = """SELECT %s FROM %s""" % (tablename, ",".join([col for col in columns]))
        return self.get_rows(self.curs, stmt, nrows)
                 
        
    def select(self, stmt):
        if self.curs is None:
            self.curs = self.conn.cursor()
        else:
            pass
        if sqlite3.complete_statement(stmt):
            return self.get_rows(self.curs, stmt, nrows)    
        else:
            print("statment invalid: %s " % stmt)
        
        
    def get_rows(self, cursor, stmt, row="last"):
        
        try:
            cursor.execute(stmt)
        except Exception as err:
            print(err)
        else:
            if type(row) is str:
                if row.lower() == "last":
                    try:
                        ID = cursor.lastrowid
                    except Exception:
                        try:
                            ID = cursor.fetchall()
                        except Exception as err:
                            print(err)
                        else:
                            return len(ID)       
                    else:
                        return ID
                elif row.lower() == "first":
                    ID = cursor.fetchone()[0]
                    cursor.close()
                    return ID
                elif row.lower() == "all":
                    ID = cursor.fetchall()
                    cursor.close()
                    return ID
                elif row.lower() == "top5":
                    ID = curs.fetchmany(5)[0]
                
            elif type(row) is int:
                ID = cursor.fetchmany(row)[0]
                return ID
            elif type(row) is tuple:
                ID = cursor.fetchmany(30)
                if row[1] in ID:
                    return True
                else:
                    return False
            else:
                print("'row' argument invalid. see docs.")
            
        
        
    def close(cursor=True, connection=False):
        if cursor is True:
            try:
                self.curs.close()
            except Exception as err:
                print(err)
                pass
            else:
                self.curs = None
                print("Cursor closed.")
        else:
            if curs is not None:
                print("Cursor is Open.")
            else:
                pass
            
        if connection is True:
            try:
                self.conn.close()
            except Exception as err:
                print(err)
                pass
            else:
                self.conn = None
                print("Connection Closed")
        else:
            if self.conn is not None:
                print("Connection is Open.")
            else:
                pass
            
        
    
    