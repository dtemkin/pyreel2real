'''
@author: Dan Temkin
@email: 


'''
from plotly.offline import plot as offplot
import plotly.graph_objs as graphs
from pandas import DataFrame, read_csv
import numpy as np
from data import Data, Database


class Plot(object):


    def __init__(self, predicted_y, actual_y):
        self.y0 = predicted_y
        self.y1 = actual_y
        self.average_precision


    def model_performance(self, recall, precision):
        box0 = dict(type="box", y=precision, boxmean="sd",
                    name="Recall", marker={"color": "#9d87ed"},
                    xaxis="x1", yaxis="y2")
        box1 = dict(type="box", y=recall, boxmean="sd",
                    name="Precision", marker={"color": "#87aaed"},
                    xaxis="x1", yaxis="y2")
        fig = graphs.Figure({"data": [box0, box1], "layout": {"showlegend": False, "title": "Accuracy Metrics"}})
        offplot(fig)

    def decision_boundary(self, boundary_function, **settings):
        boundfunc = boundary_function

        colorx_pts = settings.get("colorA_bg", "#0C48B4")
        colory_pts = settings.get("colorB_bg", "#9e2121")
        colorx_bg = settings.get("colorA_pts", "#216f9e")
        colory_bg = settings.get("colorB_pts", "#d05757")
        line_color = settings.get("boundary_color", "#2A2A2A")
        line_width = settings.get("boundary_width", "0.25")


