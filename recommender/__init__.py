import numpy as np
from pandas import DataFrame, concat
import string
from sklearn.preprocessing import LabelEncoder, MultiLabelBinarizer
from sklearn.linear_model.logistic import LogisticRegression
from sklearn.pipeline import Pipeline
encoder_log = {}

class Preprocessor(object):

    def __init__(self, df, dfname, **kwargs):
        self._encoder_name = kwargs.get("encoder_name", "multbin")
        self._encoder = None
        self._custom_encoder = kwargs.get("custom_encoder", None)
        self.dfname = dfname

        self.df = DataFrame(df)

        if self.dfname in [k for k in encoder_log.keys()]:
            self.log = encoder_log[self.dfname]
        else:
            encoder_log.update({self.dfname:{}})
            self.log = encoder_log[self.dfname]

    def _embedded_array(self, x):
        if type(x[0]) is list or type(x[0]) is tuple:
            return True
        elif type(x[0]) is str:
            if x[0].find("|") > -1:
                return "|"
            else:
                return False
        elif type(x[0]) is int:
            return False
        else:
            return False

    def _unique_values(self, array, existing=None):
        unique_values = []
        if self._embedded_array(x=array) is False:
            if existing is not None:
                unique_values.extend(existing)
                new = list(filter(lambda y: y not in unique_values, array))
                if len(new) > 0:
                    for n in new:
                        unique_values.append(n)

            else:
                unique_values.extend([u for u in np.unique(array)])

        elif type(self._embedded_array(x=array)) is str:
            uni = []
            if existing is not None:
                unique_values.extend(existing)
                for arr in array:
                    a = arr.split("|")
                    new = list(filter(lambda y: y not in unique_values, [i.strip() for i in a]))
                    unique_values.extend(new)
            else:
                for arr in array:
                    a = arr.split("|")
                    uni.extend([i.strip() for i in a])
            unique_values.extend([u for u in np.unique(uni)])

        elif self._embedded_array(x=array) is True:
            uni = []
            if existing is not None:
                unique_values.extend(existing)
                for arr in array:
                    new = list(filter(lambda y: y not in unique_values, arr))
                    unique_values.extend(new)
            else:
                for arr in array:
                    uni.extend(arr)
            unique_values.extend([u for u in np.unique(uni)])

        return unique_values


    def multlab_bin(self, cols, act):
        if act=="encode":
            for col in cols:
                try:
                    x = self.log[col]
                except KeyError:
                    unique_vals = self._unique_values(array=self.df[col])
                    self._encoder = MultiLabelBinarizer()
                    self.log.update({col: {"uniques": unique_vals, "enc":self._encoder}})
                    self._encoder.fit(unique_vals)
                else:
                    unique_vals = self._unique_values(array=self.df[col], existing=x["uniques"])
                    self._encoder = x["enc"]
                    self._encoder.fit(unique_vals)


            self.df.loc[:, cols] = self._encoder.fit_transform(self.df.loc[:, cols])
            orig_vals = self._encoder.inverse_transform(self.df[:, cols])

        elif act=="decode":
            try:
                x = self.log
            except KeyError:
                print("No encoder found for column 'col' %s" % x)
            else:

                self.df = x["unencoded"]

        else:
            print("Invalid %s Encoder Activity: %s" % (self._encoder_name, act))
            print("Must be either: ['encode', 'decode']")

    def custom_encoder(self, cols, act):
        for col in cols:
            if act == "encode":
                try:
                    x = self.log[col]
                except KeyError:
                    unique_vals = self._unique_values(array=self.df[col])
                    self._encoder = self._custom_encoder

                else:
                    unique_vals = self._unique_values(array=self.df[col], existing=encoder_log[col]["uniques"])
                    self._encoder = x["enc"]


                self._encoder.fit(unique_vals)
                self.df[col] = self._encoder.transform(self.df[col])
                orig = self._encoder.inverse_transform(self.df[col])
                self.log.update({
                                       col: {
                                           "uniques": unique_vals, "enc": self._encoder,
                                           "encoded": self.df[col], "unencoded": orig
                                       }
                                   })

            elif act == "decode":
                try:
                    x = self.log[col]
                except KeyError:
                    print("No encoder found for column 'col' %s" % col)
                else:

                    self.df[col] = x["unencoded"]
            else:
                print("Invalid %s Encoder Activity: %s" % (self._encoder_name, act))
                print("Must be either: ['encode', 'decode']")

    def labenc(self, cols, act):
        for col in cols:
            if act=="encode":
                try:
                    x = self.log[col]
                except KeyError:
                    unique_vals = self._unique_values(array=self.df[col])
                    self._encoder = LabelEncoder()
                else:
                    unique_vals = self._unique_values(array=self.df[col], existing=encoder_log[col]["uniques"])
                    self._encoder = x["enc"]

                self._encoder.fit(unique_vals)
                self.df[col] = self._encoder.transform(self.df[col])
                orig_vals = self._encoder.inverse_transform(self.df[col])
                self.log.update({col: {"uniques":unique_vals, "enc":self._encoder,
                                       "encoded": self.df[col], "unencoded":orig_vals}})


            elif act=="decode":
                try:
                    x = self.log[col]
                except KeyError:
                    print("No encoder found for column 'col' %s" % col)
                else:
                    self.df[col] = x["unencoded"]
            else:
                print("Invalid Encoder Activity: %s" % act)
                print("Must be either: ['encode', 'decode']")

    def encoder(self, cols, act):

        if self._encoder_name=="multbin":
            self.multlab_bin(cols=cols, act=act)
        elif self._encoder_name == "standard":
            self.labenc(cols=cols, act=act)
        elif self._encoder_name == "custom":
            if self._custom_encoder is None:
                print("Custom Encoder Not Specified")
            else:
                try:
                    self.custom_encoder(cols=cols, act=act)
                except Exception as err:
                    raise Exception(err)

        else:
            print("Invalid Encoder Activity: %s" % act)
            print("Must be either ['encode', 'decode']")


class Model(object):
    def __init__(self, training_data, testing_data=None, **kwargs):
        # if model_type not in ["classifier", "regressor"]:
        #     print("Error: invalid model_type %s \n must be %s" % (model_type, ["classifier", "regressor"]))
        # else:

        selector = kwargs.get("selector", "random")
        perc = kwargs.get("perc_train", .40)
        self.enc = MultiLabelBinarizer()
        if testing_data is None:
            training, testing = self._derive_train_test_sets(data=training_data,
                                                             selector=selector,
                                                             pct_train=perc)
        else:
            training, testing = self._derive_train_test_sets(training_data,
                                                             selector=selector,
                                                             pct_train=perc)
            testing.extend(testing_data)

        t = DataFrame(training)

        tx = DataFrame(testing)
        trainx = t.loc[:, ["release_year", "imdbVotes", "imdbRating"]]
        encframe = self.enc.fit_transform(t.loc[:, ["actors", "genres", "directors", "writers",]])
        print(t.loc[:, ["actors", "genres", "directors", "writers"]].applymap(lambda x: [i.strip() for i in x.split("|")]))

        self.trainy = t["watched"]
        self.testx = tx.loc[:, ["release_year", "actors", "genres", "directors", "writers", "imdbVotes", "imdbRating"]]
        self.testy = tx["watched"]

        # self.train_proc = Preprocessor(df=self.training, dfname="training", encoder_name=encoderx)
        # self.test_proc = Preprocessor(df=self.testing, dfname="testing", encoder_name=encoderx)

    def pipe(self):
        enc = MultiLabelBinarizer()
        clf = LogisticRegression(C=.01, solver="sag")
        enc.fit_transform(self.trainx)
        enc.fit_transform(self.testx)
        clf.fit_transform(self.trainx, y=self.trainy)
        pred = clf.predict(self.testx)
        print(pred)

    def _derive_train_test_sets(self, data, selector, pct_train):
        idx = [i for i in range(len(data))]
        ntrain = int(len(data) * pct_train)
        train_data, test_data = [], []
        if selector is "random":
            trainids = np.random.choice(idx, size=ntrain, replace=False)

            train_data.extend([data[x] for x in trainids])
            testids = set([_ for _ in idx]).difference(set([t for t in trainids]))
            test_data.extend([data[y] for y in testids])
        return train_data, test_data

