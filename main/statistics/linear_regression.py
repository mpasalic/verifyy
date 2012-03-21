import math

from main.statistics.common import Regression
from main.statistics.f_table import f_table_value

POSITIVIE_ZERO = +0.00000001

# Linear regression model
class LinearRegression(Regression):
    b_1 = 0.0
    b_0 = 0.0
    r_2 = 0.0
    points = 0
    xmin = 0.0
    xmax = 0.0
    summaryText = "Insufficient Data Available"
    
    def setRegressionFormula(self):
        self.t_count = 1
        x_expr = "(%f - %f)*t + %f" % (self.xmax, self.xmin, self.xmin);
        self.x_func = "function(t) { return %s; }" % x_expr
        self.y_func = "function(t) { return (%f)*(%s) + (%f); }" % (self.b_1, x_expr, self.b_0)
        pass
    
    def regress(self, x, y):
        self.points = len(x)
        if len(x) < 5:
            return;
        
        self.xmin = min(x)
        self.xmax = max(x)
        
        #1. Compute the regression coefficients
        n = self.points
        x_mean = 0.0
        y_mean = 0.0
        for i in range(0, self.points):
            y_mean += y[i]
            x_mean += x[i]
        y_mean = y_mean / float(len(y))
        x_mean = x_mean / float(len(x))

        sum_xy_err = 0.0
        sum_x_2_err = 0.0
        
        for i in range(0, self.points):
            sum_xy_err = (x[i]-x_mean)*(y[i]-y_mean)
            sum_x_2_err = (x[i] - x_mean)*(x[i] - x_mean)
        
        if (sum_x_2_err == 0):
            # This means that all the points are located at the same x point)
            return;
        
        self.b_1 = sum_xy_err / sum_x_2_err
        self.b_0 = y_mean - self.b_1 * x_mean
        self.setRegressionFormula()
        
        # Now, compute SSR, SSE, fo the F-test ANOVA
        SSE = 0.0
        SSR = 0.0
        n   = len(x) # number of observations
        p   = 1      # number of predictor variables
        
        for i in range(0, len(x)):
            y_predict = self.b_1 * x[i] + self.b_0
            SSE += (y_predict - y[i])*(y_predict - y[i])
            SSR += (y_predict - y_mean)*(y_predict - y_mean)
        pass
        
        #Now, r squared = SSR/(SSR + SSE)
        if (SSE < POSITIVIE_ZERO):
            # Perfect fir, r_2 is over the charts
            self.r_2 = 1.0
            self.f_value = 0.1+f_table_value(1, n-2)*10
        else:
            self.r_2 = SSR/(SSR+SSE)
            MSM = SSR / (1)
            MSE = SSE / (n - 2)
            self.f_value = MSM/MSE
            
        #Perform an f-test
        self.f_goal  = f_table_value(1, n - 2)
        
        if self.f_value > 10 * self.f_goal:
            self.veryStrongSignificance()
        elif self.f_value > self.f_goal:
            self.strongSignificance()
        else:
            self.weakSignificance()
        pass
    
    def formatSummaryText(self, keyword, oper):
        self.summaryText = "The data %s be related by a linear relationsip\
         (R=%.2f). y =  %.2fx %s. F-test: %.2f %s %.2f.\
         " % (keyword, math.sqrt(self.r_2), self.b_1, self.fmtTerm(self.b_0), self.f_value, oper, self.f_goal)
    
    def strongSignificance(self):
        self.formatSummaryText("is likely to", ">")
        pass
        
    def veryStrongSignificance(self):
        self.formatSummaryText("is highly related to", ">")
        pass
    
    def weakSignificance(self):
        self.formatSummaryText("is unlikely to be related to", "<")
        pass
    
    def summary(self):
        return self.summaryText
    