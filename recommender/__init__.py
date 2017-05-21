import numpy as np
from pandas import DataFrame, concat
import string
from sklearn.pipeline import Pipeline
encoder_log = {}


class Model(object):
    def __init__(self, training_data, testing_data=None, **kwargs):
        # if model_type not in ["classifier", "regressor"]:
        #     print("Error: invalid model_type %s \n must be %s" % (model_type, ["classifier", "regressor"]))
        # else:

        selector = kwargs.get("selector", "random")
        perc = kwargs.get("perc_train", .40)
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

