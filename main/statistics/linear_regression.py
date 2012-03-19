from stats import linregress
from main.statistics.common import Regression

class LinearRegression(Regression):
    slope = 0.0
    intercept = 0.0
    ttProb = 0.0
    r = 0.0
    points = 0
    xmin = 0.0
    xmax = 0.0
    
    def setRegressionFormula(self):
        self.t_count = 1
        x_expr = "(%f - %f)*t + %f" % (self.xmax, self.xmin, self.xmin);
        self.x_func = "function(t) { return %s; }" % x_expr
        self.y_func = "function(t) { return (%f)*(%s) + (%f); }" % (self.slope, x_expr, self.intercept)
        pass
    
    def regress(self, x, y):
        self.points = len(x)
        if len(x) >= 2:
            self.xmin = min(x)
            self.xmax = max(x)
            self.slope, self.intercept, self.r, self.ttProb, sterr = linregress(x, y)
            self.setRegressionFormula()
        pass
    
    def summary(self):
        if self.points == 0 :
            return "No Data Available"
        elif self.points < 2:
            return "Insufficient Data Available"
        else:
            likely = "may"
            if (self.r < 0.2):
                likely = "is unlikely to"
            return "The data %(likely)s be linearly related (r=%(r).2f). y =  %(slope).2fx + %(intercept).2f" % \
                {"slope": self.slope, "intercept": self.intercept, "p": self.ttProb, "r": self.r, "likely": likely}
