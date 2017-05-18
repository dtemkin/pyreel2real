from data import Data, Database, fandango
from sqlite3 import OperationalError
from utils import fullpath
import statistics as stats
from pandas import DataFrame, read_csv
import numpy as np
from sklearn.pipeline import Pipeline
import os


labeled_movies = []
def prepare():
    db = Database(fullpath("data/data.db"))
    data = Data(mediatype="movie")

    titles = data.titles_list()
    try:
        select_existing = db.select(table="main", fields="all")
    except OperationalError:
        data.collect(args=data.titles_list(), addtl_items=["boxoffice", "oscars", "review"])
        i = 0
        for movie in labeled_movies:
            if i == 0:
                print("Making Table main")
                db.make_table(table="main", fields=[k for k in movie.keys()])
            else:
                pass
            db.update(row=movie)
            db.conn.commit()
            i += 1
    else:
        if len(select_existing) == len(titles):
            header = select_existing[0].keys()
            for x in select_existing:
                labeled_movies.append(dict(map(lambda x, y: (x, y), header, x)))

        else:
            data.collect(args=data.titles_list(), addtl_items=["boxoffice", "oscars", "review"])
            i = 0
            for movie in labeled_movies:
                if i == 0:
                    print("Making Table main")
                    db.make_table(table="main", fields=[k for k in movie.keys()])
                else:
                    pass
                db.update(row=movie)
                db.conn.commit()
                i += 1

x_vars = ["release_year", "mpaa_rating", "genres", "actors", "directors", "imdbRating", "imdbVotes"]
y_vars = "watched"

from sklearn.preprocessing import OneHotEncoder, LabelEncoder
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import SGDClassifier
from sklearn.metrics import recall_score, accuracy_score
enc = OneHotEncoder()

encoder_log = {}

def convert_features(d, cat, **kwargs):
    colnames = kwargs.get("colnames")
    df = DataFrame(d, columns=colnames).dropna(thresh=3)
    uni = []
    nn = []
    nx = []

    if cat in [k for k in encoder_log.keys()]:
        uni.extend(encoder_log[cat]["unique_vals"])

    else:
        for g in df[cat]:
            uni.extend(g.split("|"))

    unique = np.unique(uni)
    other_count = 0

    fromunique_map = dict(map(lambda x: (unique[x], x + 1), [u for u in range(len(unique))]))
    tounique_map = dict(map(lambda x: (x + 1, unique[x]), [u for u in range(len(unique))]))
    encoder_log.update({cat: {"unique_vals": unique, "from_unique": fromunique_map, "to_unique": tounique_map, "other_count":other_count}})

    for gx in df[cat]:
        z = [0] * (len(unique))

        if type(gx) is float:
            pass
        else:
            gg = gx.split("|")

            for t in gg:
                try:
                    ii = fromunique_map[t]
                except KeyError:
                    pass
                else:
                    z[ii-1] += 1

        nn.append(z)

    df[cat+"_enc"] = nn
    return df

def build_arrays(df, cols):
    arrs = []

    for col in cols:
        arr = np.vstack(tuple(list(map(lambda x: np.array(x), df[col]))))
        arrs.append(arr)
    a = np.hstack(tuple([e for e in arrs]))
    return a


prepare()

model0 = DecisionTreeClassifier(criterion="entropy")
model1 = RandomForestClassifier(criterion="entropy", n_estimators=50)

in_theaters = fandango.Theater()

if os.path.isfile(fullpath("data/fandango.csv")):
    lst = ["ID","actors","boxoffice_todate","countries","directors",
           "dvd_release","genres","imdbID","imdbRating","imdbVotes",
           "langs","mpaa_rating","plot","poster_url","prodco",
           "release_date","release_year","runtime",
           "title","writers","watched"]

    unlabeled_movies = read_csv(fullpath("data/fandango.csv"), index_col=0)




else:
    lst = in_theaters.listings()
    in_theaters.save(data=lst)
    unlabeled_movies = lst


train_df = convert_features(d=labeled_movies, cat="genres")
test_df = convert_features(d=unlabeled_movies, cat="genres")
for h in ["mpaa_rating", "actors", "directors"]:
    train_df = convert_features(d=train_df, cat=h)
    test_df = convert_features(d=test_df, cat=h)

train_df["imdbRating"] = list(map(lambda x: int(float(train_df.loc[x]["imdbRating"]) * 10), [idx for idx in train_df.index]))
test_df["imdbRating"] = list(map(lambda x: int(float(test_df.loc[x]["imdbRating"]) * 10), [idx for idx in test_df.index]))
train_df["imdbVotes"] = list(map(lambda x: int(float(train_df.loc[x]["imdbVotes"])), [idx for idx in train_df.index]))
test_df["imdbVotes"] = list(map(lambda x: int(float(test_df.loc[x]["imdbVotes"])), [idx for idx in test_df.index]))


trainx = build_arrays(df=train_df.loc[:, ["genres_enc", "mpaa_rating_enc", "actors_enc", "directors_enc", "imdbRating", "imdbVotes"]], cols=["genres_enc", "mpaa_rating_enc", "actors_enc", "directors_enc", "imdbRating", "imdbVotes"])
trainx_text = train_df.loc[:, ["title", "poster_url", "genres", "mpaa_rating", "actors", "directors", "imdbRating", "imdbVotes"]]
trainy = build_arrays(train_df.loc[:, ["watched"]], ['watched'])


testx = build_arrays(df=test_df.loc[:, ["genres_enc", "mpaa_rating_enc", "actors_enc", "directors_enc", "imdbRating", "imdbVotes"]], cols= ["genres_enc", "mpaa_rating_enc", "actors_enc", "directors_enc", "imdbRating", "imdbVotes"])
testx_text = test_df.loc[:, ["title", "poster_url", "plot", "genres", "mpaa_rating", "actors", "directors", "imdbRating", "imdbVotes"]]
testy = build_arrays(unlabeled_movies.loc[:, ["watched"]], ["watched"])


def execute():
    pipe = Pipeline([("enc", OneHotEncoder()),
                     ("clf", DecisionTreeClassifier(criterion="entropy"))])
    pipe.fit(X=trainx, y=trainy)
    pred = pipe.predict(X=testx)
    confirm(predicted=pred, actual=testy)

def confirm(predicted, actual):
    b=0
    accs = []
    recs = []
    while b <= 20:
        ids = np.random.choice([x for x in range(0, len(actual))], size=int(1*len(actual)))
        acc = accuracy_score([int(actual[x]) for x in ids], [int(predicted[i]) for i in ids])
        recall = recall_score([int(actual[x]) for x in ids], [int(predicted[i]) for i in ids])
        accs.append(acc)
        recs.append(recall)
        b+=1
    avg_acc = stats.mean(accs)
    avg_recall = stats.mean(recs)
    print(avg_acc, avg_recall)
execute()
