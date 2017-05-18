from utils import fullpath
import os
import csv

datadir = fullpath("data/files/movielens/")
filenames = ["u.data","u.genre","u.info","u.item","u.occupation","u.user"]
datafiles = list(map(lambda x: os.path.join(datadir, x), filenames))

class Data(object):

    def __init__(self, sep="|"):
        self.sep = sep
        self.datadir = fullpath("data/movielens/")

    def _read_tabfile(self, file):
        with open(file, mode="r") as fx:
            readx = csv.reader(fx, delimiter=self.sep)
            next(readx)
            for row in readx:
                yield row

    def genres_map(self):
        filex = os.path.join(self.datadir, "u.genre")
        vals = list(next(self._read_tabfile(file=filex)))
        return vals

    def items(self):
        filex = os.path.join(self.datadir, "u.item")
        val = next(self._read_tabfile(file=filex))

    def users_info(self):
        filex = os.path.join(self.datadir, "u.user")
        val = next(self._read_tabfile(file=filex))

    def occupations_list(self):
        filex = os.path.join(self.datadir, "u.occupation")
        vals = list(next(self._read_tabfile(file=filex)))
        return vals
    def __iter__(self):
        filex = os.path.join(self.datadir, "u.data")
        yield self._read_tabfile(file=filex)
