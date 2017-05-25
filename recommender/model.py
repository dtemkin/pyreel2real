from pandas import DataFrame, read_csv, concat
import numpy as np
from sklearn.preprocessing import OneHotEncoder
from data import Data, Database, fandango, FeatureMap
from utils import fullpath
from sqlite3 import OperationalError
import os
from statistics import mean
from recommender.performance import Metrics
from sklearn.feature_selection import SelectFromModel, RFE
from sklearn.model_selection import cross_val_score, StratifiedKFold, KFold

encoder_log = {}

cols_master = ["release_year"]


class Preprocessor(object):

    def __init__(self, x_vars, y_vars, **kwargs):
        self.x_vars, self.y_vars = x_vars, y_vars
        self.encoder = kwargs.get("encoder", OneHotEncoder())
        self.folds = []
        self.labeled = []
        self.unlabeled = []


    def _derive_sets(self, data, **kwargs):
        selector = kwargs.get("selector", "random")
        pct_train = kwargs.get("percent_train", .75)
        sz = kwargs.get("size", 1.0)

        idx = [i for i in range(len(data))]
        nrows = int(len(idx)*sz)
        avail = np.random.choice(idx, size=nrows, replace=True)
        ntrain = int(nrows*pct_train)

        train_data, test_data = [], []
        if selector is "random":
            trainids = np.random.choice(avail, size=ntrain, replace=True)
            train_data.extend([data[x] for x in trainids])
            testids = [_ for _ in idx]
            test_data.extend([data[y] for y in testids])
        return train_data, test_data

    def _pseudo_cases(self, data, n, classx):

        dx = [data[i] for i in list(filter(lambda x: data[x]["watched"]==classx, [i for i in range(len(data))]))]
        pseudo_cases=[]
        for i in range(n):
            case={"title":"FAKE", "watched": classx}
            for col in self.x_vars:
                x = np.random.choice([d for d in range(len(dx))])
                case.update({col: data[x][col]})
            pseudo_cases.append(case)
        data.extend(pseudo_cases)
        return data



    def encoded_df(self, d, cats, **kwargs):
        df = DataFrame(d, columns=self.x_vars)
        for cat in cats:
            features = FeatureMap(refmap=cat)
            mapped = []
            text_map = []
            enc_map = []
            for row_values in df[cat]:
                enc_vals = np.zeros(len(features.get_valuemap(index_on="id")), dtype=np.int64)
                if type(row_values) is float:
                    pass
                elif type(row_values) is str:
                    text_vals = [r.strip() for r in row_values.split("|")]
                    vals = features.lookup_values(by="values", values=text_vals)
                    mapped.append([int(v) for v in vals])
                    text_map.append(text_vals)
                    for v in vals:
                        try:
                            enc_vals[int(v)] += 1
                        except IndexError:
                            pass
                        else:
                            pass
                else:
                    print(row_values)

                enc_map.append(enc_vals)

            df[cat] = enc_map
        return df

    def build_arrays(self, df):
        arrs = []
        for col in self.x_vars:
            arr = np.vstack(tuple(list(map(lambda x: np.array(x, dtype=np.float64), df[col]))))
            arrs.append(arr)
        a = np.hstack(tuple([e for e in arrs]))
        return a

    def _get_labeled(self, pseudo_count):
        db = Database(fullpath("data/data.db"))
        data = Data(mediatype="movie")
        titles = data.titles_list()
        labeled = []
        try:
            select_existing = db.select(table="main", fields="all")
        except OperationalError:
            data.collect(args=data.titles_list(), addtl_items=["boxoffice", "oscars", "review"])
            i = 0
            for movie in labeled:
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
                    labeled.append(dict(map(lambda x, y: (x, y), header, x)))

            else:
                data.collect(args=data.titles_list(), addtl_items=["boxoffice", "oscars", "review"])
                i = 0
                for movie in labeled:
                    if i == 0:
                        print("Making Table main")
                        db.make_table(table="main", fields=[k for k in movie.keys()])
                    else:
                        pass
                    db.update(row=movie)
                    db.conn.commit()
                    i += 1

        lab = self._pseudo_cases(data=labeled, n=pseudo_count, classx="0")
        return lab

    def get_unlabeled(self, pseudo_count):
        in_theaters = fandango.Theater()

        if os.path.isfile(fullpath("data/fandango.csv")):
            lst = ["ID", "actors", "boxoffice_todate", "countries", "directors",
                   "dvd_release", "genres", "imdbID", "imdbRating", "imdbVotes",
                   "langs", "mpaa_rating", "plot", "poster_url", "prodco",
                   "release_date", "release_year", "runtime",
                   "title", "writers", "watched"]

            unlabeled = read_csv(fullpath("data/fandango.csv"), index_col=0)
        else:
            lst = in_theaters.listings()
            in_theaters.save(data=lst)
            unlabeled = lst

        unlab = self._pseudo_cases(data=unlabeled.to_dict(orient="records"), n=pseudo_count, classx=0)
        return unlab

    def set_trials(self, count, size, pseudo_count, perc_train, selector="random"):
        trials = []
        data = self._get_labeled(pseudo_count=pseudo_count)

        for i in range(count):
            train, test = self._derive_sets(data=data, size=size, selector=selector, percent_train=perc_train)
            trials.append({"n":i, "train":train, "test":test})
        return trials

class Model(Preprocessor):

    def __init__(self, classifier, **kwargs):
        self.target_cols = kwargs.get("target_cols", ["watched"])
        self.var_cols = kwargs.get("var_cols", ["release_year", "actors", "genres", "imdbVotes", "imdbRating"])
        self.categorical_vars = ["actors", "genres"]
        self.clf = classifier

        self.test_metrics = None
        self.train_metrics = None
        self.labeled_crxval = None
        self.unlabeled_crxval = None
        super().__init__(self.var_cols, self.target_cols)


    def prep_unlabeled(self, pseudo_count=40):
        unlab = self.get_unlabeled(pseudo_count)
        unlab_x = self.encoded_df(d=unlab, cats=self.categorical_vars)
        unlab_xarrs = self.build_arrays(unlab_x.dropna(thresh=3).fillna(0.))
        unlab_y = [str(unlab[u]["watched"]) for u in range(len(unlab))]
        return unlab_xarrs, unlab_y

    def prep_labeled(self, X):
        # Encode labeled training dataframe, converting categorical variables to binary
        x = self.encoded_df(X, cats=self.categorical_vars)
        # Coerce labeled training dataframe to set of arrays
        x_arrs = self.build_arrays(x)
        # Extract response variable
        y = [str(i["watched"]) for i in X]
        return x_arrs, y

    def rebuild_class_array(self, clf, test_set, rtn="avg"):
        # Get array predicted probability values using "labeled" testing data
        lprobs = self.predict_probs(clf=clf, xarray=test_set)

        avg_lprobs = {"0": float(mean([n[0] for n in lprobs])), "1": float(mean([n[1] for n in lprobs]))}
        # rebuild predicted classes using probabilities
        lpx = []
        for lp in lprobs:
            if lp[0] > lp[1]:
                lpx.append(0)
            elif lp[1] > lp[0]:
                lpx.append(1)
            else:
                # If neither is greater then use random selection
                rand_label = np.random.choice([0, 1], size=1)
                lpx.append(rand_label[0])

        print("\n\nEstimated Average Class Probabilities:")
        print("0: \t\t %s" % avg_lprobs["0"])
        print("1: \t\t %s" % avg_lprobs["1"])
        if rtn == "avg":
            return avg_lprobs, lpx
        else:
            return list(map(lambda y: {"0": y[0], "1": y[1]}, [n for n in lprobs])), lpx

    def reclassify(self, old_clf, class_wts, trainx, trainy):
        # Apply probabilities from labeled data to new classifier
        new_clf = old_clf.set_params(class_weight=class_wts)
        # Refit using new probabilities
        new_clf.fit(trainx, trainy)
        return new_clf

    def run(self, **kwargs):
        metrics = []

        xfold_count = kwargs.get("crossfolds_count", 1)
        xfold_size = kwargs.get("crossfolds_size", 1.0)
        xfold_train = kwargs.get("percent_train", .75)
        xfold_select = kwargs.get("selector", "random")
        fake_cnt_labeled = kwargs.get("labeled_pseudo_count", 1000)
        fake_cnt_unlabeled = kwargs.get("unlabeled_pseudo_count", 40)

        trials = self.set_trials(count=xfold_count, size=xfold_size, selector=xfold_select, pseudo_count=fake_cnt_labeled, perc_train=xfold_train)
        # Run trial sequence
        unlabeled_x, unlabeled_y = self.prep_unlabeled(pseudo_count=fake_cnt_unlabeled)

        for t in range(len(trials)):

            print("Trial - %s of %s" % (t+1, len(trials)))

            trainx, trainy = self.prep_labeled(X=trials[t]["train"])
            testx, testy = self.prep_labeled(X=trials[t]["test"])
            # Get array predicted class values using "labeled" training data
            train_pred, clf = self.predict_training(train_x=trainx, train_y=trainy, test_x=testx)

            print("Labeled Data Metrics")
            # Get training data classification report for
            # classes 0/1/total|avg (Accuracy, Precision, F1, Support)
            print("Classification Report")
            wts, cls_arr = self.rebuild_class_array(clf=clf, test_set=testx)
            train_metrics = Metrics(testy)
            self.train_metrics = train_metrics.__dict__()
            self.train_metrics.cls_report(predicted_y=train_pred, target_classes=["0","1"])
            print(self.train_metrics["classification_report"])


            print("Cross-Validation:\n")
            self.labeled_crxval.extend(self.cross_validation(clf=clf, x=trainx, y=trainy))
            print(self.labeled_crxval)

            self.train_metrics.roc_auc_score(true_y=[int(u) for u in testy], score_y=cls_arr)
            self.train_metrics.roc_curve(true_y=[int(u) for u in testy], score_y=cls_arr)
            print("\nROC:")
            print("\tAUC: %s" % self.train_metrics["auc_score"])
            print("\tFPR: %s" % self.train_metrics["false_pos_rate"])
            print("\tTPR: %s" % self.train_metrics["true_pos_rate"])
            print("\n\n")



            new_clf = self.reclassify(old_clf=clf, class_wts=wts, trainx=trainx, trainy=trainy)
            # Get predicted values using "unlabeled" data
            test_pred = self.predict_testing(new_clf, unlabeled_x)


            print("Unlabeled Data Metrics")
            print("Classification Report")
            test_metrics = Metrics(unlabeled_y)
            self.test_metrics = test_metrics.__dict__()
            self.test_metrics.cls_report(test_pred, target_classes=["0","1"])
            print(self.test_metrics["classification_report"])
            ulwts, ulcls_arr = self.rebuild_class_array(clf=new_clf, test_set=unlabeled_x)

            print("Cross-Validation:\n")
            self.unlabeled_crxval.extend(self.cross_validation(clf=new_clf, x=unlabeled_x, y=unlabeled_y))

            print(self.unlabeled_crxval)

            self.test_metrics.roc_auc_score(true_y=[int(u) for u in unlabeled_y], score_y=ulcls_arr)
            self.test_metrics.roc_curve(true_y=[int(u) for u in unlabeled_y], score_y=ulcls_arr)
            print("\nROC:")
            print("\tAUC: %s" % self.test_metrics["auc_score"])
            print("\tFPR: %s" % self.test_metrics["false_pos_rate"])
            print("\tTPR: %s" % self.test_metrics["true_pos_rate"])
            print("\n\n")

            print("\n\n")


    def cross_validation(self, clf, x, y, cv=10):
        crx_valid = cross_val_score(clf, x, y, cv=cv)
        return crx_valid

    def predict_training(self, train_x, train_y, test_x):
        self.clf.fit(train_x, train_y)
        pred = self.clf.predict(test_x)
        return pred, self.clf

    def predict_testing(self, fitted_clf, test_x):
        pred = fitted_clf.predict(test_x)
        return pred

    def predict_probs(self, clf, xarray, **kwargs):
        logprob = kwargs.get("log", False)
        if logprob is True:
            probarr = clf.predict_log_proba(xarray)
        else:
            probarr = clf.predict_proba(xarray)
        return probarr


    def __call__(self):
        return self.run()


from sklearn.tree import DecisionTreeClassifier
from sklearn.linear_model import LogisticRegression, SGDClassifier
from sklearn.ensemble import RandomForestClassifier
print("Decision Tree Classifier:\n")
mod1 = Model(classifier=DecisionTreeClassifier(random_state=0))
mod1.run()

plt = Plot()
plt.positive_rates(tpr_array=mod1.test_metrics["true_pos_rate"], fpr_array=mod1.test_metrics["false_pos_rate"])

print("\n\nRandom Forest Classifier:\n")
mod1x = Model(classifier=RandomForestClassifier())
mod1x.run()

print("\n\nLogistic Regression:\n")
mod2 = Model(classifier=LogisticRegression(n_jobs=3))
mod2.run()
