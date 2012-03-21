from main.statistics.common import Analysis
from main.statistics.pvalue import chi_square_p_value
import math


# ChiSquareFTest:
#   We have a collection of observations, x & y are discrete
#   
#
#   Use Chi-squared test with F-test
#   TODO: Use conditional entropy to try to see if there's any information gain
#
#

POSTIVE_ZERO=+0.00000000001

class ChiSquareTest(object):
    summaryText = "Insufficient Data Available"
    
    def __init__(self, classesX, classesY):
        super(ChiSquareTest, self).__init__()
        # Intialize a table of level to points for that level
        self.table = {}
        self.xbins = {}
        self.ybins = {}
        self.classesX = classesX
        self.classesY = classesY
        for clsX in classesX:
            self.table[clsX] = {}
            self.xbins[clsX] = 0
            for clsY in classesY:
                self.table[clsX][clsY] = 0
                self.ybins[clsY] = 0
    
    def analyse(self, data):
        # record the discrete data into the correct bin
        total = 0
        x_bins = self.xbins
        y_bins = self.ybins
        
        for datum in data:
            self.table[datum.x][datum.y] += 1
            total += 1
            x_bins[int(datum.x)] += 1
            y_bins[int(datum.y)] += 1
        
        if (total == 0):
            # This means we have no data
            return
        
        total = float(total)
        
        null_hypothesis = {}
        for xi in self.classesX:
            null_hypothesis[xi] = {}
            for yi in self.classesY:
                null_hypothesis[xi][yi] = x_bins[xi] * y_bins[yi] / total
        
        # Now, perform Chi-Square
        chi_square = 0.0
        for xi in self.classesX:
            for yi in self.classesY:
                e_ij = (null_hypothesis[xi][yi] - self.table[xi][yi])
                chi_square += e_ij * e_ij / null_hypothesis[xi][yi]
        
        df = (len(self.classesX)-1) * (len(self.classesY)-1)
        self.pval = chi_square_p_value(df, chi_square)
        self.chi_square = chi_square
        
        # Note that these if statements were specifically coded to avoid
        # potential division by 0
        if (self.pval < 0.01):
            self.veryStrongSignificance()
        elif (self.pval < 0.10):
            self.strongSignificance()
        else:
            self.weakSignificance()
        pass
        
    def formatSummaryText(self, keyword):
        self.summaryText = "The association between variables %s (p = %.2f, X<sup>2</sup>=%.2f)." % (keyword, self.pval, self.chi_square)
        
    def strongSignificance(self):
        self.formatSummaryText("is likely to be present")
        pass
        
    def veryStrongSignificance(self):
        self.formatSummaryText("is highly likely to be present")
        pass
    
    def weakSignificance(self):
        self.formatSummaryText("is inconclusive or unlikely")
        pass
        
    def summary(self):
        return self.summaryText

