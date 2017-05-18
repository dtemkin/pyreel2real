
class Movie(object):

    def __init__(self, **attrs):
        self._dict = dict()

    def build(self, **attrs):
        for k, v in dict(**attrs).items():
            if k not in [i for i in self._dict.keys()]:
                self._dict.update({k: v})
            else:
                pass


    def __call__(self):
        return self._dict


class Movies(object):

    def __init__(self):
        self._movies = list()
    def __call__(self):
        return self._movies

class TV(object):

    def __init__(self, **attrs):
        pass
