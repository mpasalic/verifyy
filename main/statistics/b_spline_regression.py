# # # # # # # # # # # # # # # # # # # # # # # # # # # #
# @author Alexander Novikov
#
# This is the main driver class for b-spline regression
# using the hard work of several other files
# 

from main.statistics.common import Regression
from main.statistics.f_table import f_table_value
from main.statistics.geom2d import cluster, point
from main.statistics.heuristic_clustering import do_cluster1, do_cluster2
from main.statistics.splines import b_spline

class BSplineRegression(Regression):
    # number of points in using when approximating R^2, ANOVA F-test
    approximationPoints = 1000
    
    # kN corresponds to kN * x^N term
    xmin = 0.0
    xmax = 0.0
    r_2 = 0.0
    summaryText = "Insufficient Data Available"
    
    
    # This method 
    def setRegressionFormula(self, curve):
        curve.generateEquationList()
        self.x_func = curve.x_func
        self.y_func = curve.y_func
        self.t_count = curve.t_count
        pass
    
    def summary(self):
        return self.summaryText
    
    def formatSummaryText(self, keyword, oper):
        pass
    
    def strongSignificance(self):
        self.formatSummaryText("is likely to", ">")
        pass
        
    def veryStrongSignificance(self):
        self.formatSummaryText("is highly related to", ">")
        pass
    
    def weakSignificance(self):
        self.formatSummaryText("is unlikely to be related to", "<")
        pass
    
    def analyse(self, data):
        # We don't have enough data to do ANOVA
        if len(data) < 5:
            return
        
        points = []
        for datapt in data:
            points.append(point(datapt.x, datapt.y))
        
        #1. Make sure x, y lengths are learge enough 
        confidence_thresh   = 0.66
        stddev_thresh       = 1.0
        decay_thresh        = 1.0
        clusters = do_cluster1(points, confidence_thresh, stddev_thresh, decay_thresh)
        params   = do_cluster2(clusters)
        
        clusters = params['clusters']
        
        curve = b_spline(params)
        
        self.setRegressionFormula(curve)
        
        #predictions = curve.evalPoints(self.approximationPoints)
        
        # TODO: Now use the prediction values to compute F-test, R^2
        pass
            
        