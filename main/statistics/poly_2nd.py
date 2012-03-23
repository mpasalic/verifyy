# # # # # # # # # # # # # # # # # # # #
# @author Alexander Novikov
#
# Implementation of 2nd order polynomial regression over data
# Uses r_2 rsquared values, F_value and F_goal for F-test
#
#

from main.statistics.common import Regression
from main.statistics.gauss import ge_solve
from main.statistics.f_table import f_table_value

POSITIVE_ZERO = 0.000000001

class Poly2OrderRegression(Regression):
    # kN corresponds to kN * x^N term
    k0 = 0.0
    k1 = 0.0
    k2 = 0.0
    xmin = 0.0
    xmax = 0.0
    r_2 = 0.0
    summaryText = "Insufficient Data Available"
    
    # This method 
    def setRegressionFormula(self):
        self.t_count = 1
        x_expr = "(%f)*t + %f" % (self.xmax - self.xmin, self.xmin);
        x_shifted = "(%f)*t" % (self.xmax - self.xmin)
        self.x_func = "function(t) { return %s; }" % x_expr
        self.y_func = "function(t) { return (%f)*(%s)*(%s) + (%f)*(%s) + %f; }" % (self.k2, x_shifted, x_shifted, self.k1, x_shifted, self.k0)
        pass
    
    def summary(self):
        return self.summaryText
    
    def formatSummaryText(self, keyword, oper):
        self.summaryText = "The data %s be related by a second-order polynomial\
         (R<sup>2</sup>=%.2f). y =  %.3g(x - %.3g) <sup>2</sup> %s(x - %.3g) %s. F-test: %.2f %s %.2f.\
         " % (keyword, self.r_2, self.k2, self.xmin, self.fmtTerm(self.k1), self.xmin, self.fmtTerm(self.k0), self.f_value, oper, self.f_goal)
    
    def strongSignificance(self):
        self.formatSummaryText("is likely to", ">")
        pass
        
    def veryStrongSignificance(self):
        self.formatSummaryText("is highly related to", ">")
        pass
    
    def weakSignificance(self):
        self.formatSummaryText("is unlikely to be related to", "<")
        pass
    
    def regress(self, x, y):
        # We don't have enough data to do ANOVA
        if len(x) < 5 or len(y) < 5:
            return
        
        #1. Make sure x, y lengths are learge enough
        
        #2. Compute the coefficients of the matrix to solve
        x_2 = []
        x_3 = []
        x_4 = []
        
        self.xmin = min(x)
        self.xmax = max(x)
        
        for i in range(0, len(x)):
            x[i] = x[i] - self.xmin
            
        y_mean = 0
        
        # Compute sums of powers of X
        for i in range(0, len(x)):
            y_mean += y[i]
            x_2.append(   x[i] * x[i] )
            x_3.append( x_2[i] * x[i] )
            x_4.append( x_3[i] * x[i] )
        pass
        
        # Get the grand mean of y
        y_mean = y_mean / len(x)
        
        m_00 = sum(x_4)  
        m_01 = sum(x_3)
        m_02 = sum(x_2)
        y_0  = sum( map(lambda i: x_2[i]*y[i], range(0, len(x))) )
        m_10 = sum(x_3)
        m_11 = sum(x_2)
        m_12 = sum(x)
        y_1  = sum( map(lambda i: x[i]*y[i], range(0, len(x))) )
        m_20 = sum(x_2)
        m_21 = sum(x)
        m_22 = len(x) * 1.0
        y_2  = sum(y)
        
        M = [
            [m_00, m_01, m_02],
            [m_10, m_11, m_12],
            [m_20, m_21, m_22]
        ]
        
        Y = [y_0, y_1, y_2]
        
        # Solve for the model coefficients using Gaussian Elemination
        try :
            X = ge_solve(M, Y)
        except Exception as e:
            # This means Matrix was not of full rank (degenerate points)
            # Enforce waiting for more data
            return
        
        # Output regression coefficients
        self.k2 = X[0]
        self.k1 = X[1]
        self.k0 = X[2]
        
        # Set javascipt function computation code
        self.setRegressionFormula()
        
        # Now, compute SSR, SSE, fo the F-test ANOVA
        SSE = 0.0
        SSR = 0.0
        n   = len(x) # number of observations
        p   = 1      # number of predictor variables
        
        for i in range(0, len(x)):
            y_predict = self.k2 * x[i]*x[i] + self.k1*x[i] + self.k0
            SSE += (y_predict - y[i])*(y_predict - y[i])
            SSR += (y_predict - y_mean)*(y_predict - y_mean)
        pass
        
        #Now, r squared = SSR/(SSR + SSE)
        if (abs(SSE) < POSITIVE_ZERO):
            # This is a perfect fit model
            self.r_2 = 1
            self.f_value  = 0.1+10*f_table_value(1, n - 2)
        else:
            self.r_2 = SSR/(SSR+SSE)
        
            #Perform an f-test
            MSM = SSR / (1)
            MSE = SSE / (n - 2)
            self.f_value = MSM/MSE
        
        self.f_goal  = f_table_value(1, n - 2)
        
        if self.f_value > 10 * self.f_goal:
            self.veryStrongSignificance()
        elif self.f_value > self.f_goal:
            self.strongSignificance()
        else:
            self.weakSignificance()
        
        pass
        