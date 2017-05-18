'''
Created on Jan 9, 2017

@author: dysmas
'''
import os
from useragentx.useragent import spoof


def fullpath(filename):
    return os.path.abspath(os.path.join(os.path.dirname(__file__), filename))

useragent = spoof().browser("Chrome", 0)

