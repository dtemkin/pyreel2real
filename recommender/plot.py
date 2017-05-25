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


    def __init__(self, y0, y1):
        self.y0 = y0
        self.y1 = y1


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

    def _boundary(self, x_vec, mu_vec1, mu_vec2):
        g1 = (x_vec - mu_vec1).T.dot((x_vec - mu_vec1))
        g2 = 2 * ((x_vec - mu_vec2).T.dot((x_vec - mu_vec2)))
        return g1 - g2


    def positive_rates(self, tpr_array, fpr_array, yscale=list([0., 1.])):
        line0 = graphs.Scatter(y=fpr_array, markers="line")
        line1 = graphs.Scatter(y=tpr_array, markers="line")




    def cross_validations(self, cv_array):
        xvals = [i for i in range(len(cv_array))]
        yvals = cv_array