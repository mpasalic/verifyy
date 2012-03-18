# # # # # # # # # # # # # # #
# @author Alexander Novikov
#
# This is an implementation of
# One Factor Analysis :
#   x data is whole numbers representing a finite collection of labels
#   y data is real numbers
#
#

import math
from main.statistics.common import Analysis
from main.statistics.f_table import f_table_value

# One Factor Analysis :
#   x data is whole numbers representing a finite collection of labels
#   y data is real numbers
class OneFactorAnalysis(Analysis):
    def __init__(self, classes):
        super(OneFactorAnalysis, self).__init__()
        # Intialize a table of level to points for that level
        self.levels = {}
        self.stdDev1Intervals = {}
        for cls in classes:
            self.levels[cls] = []
    
    
    def find1StdDevIntervals(self):
        # We already have the means, simply compute
        stdDev1Intervals = {}
        means = self.means
        lvls = self.levels
        for cls in self.levels:
            e_j = sum( map(lambda y: (y - self.means[cls])*(y - self.means[cls]), self.levels[cls]) )
            e_j = math.sqrt( e_j / len(self.levels[cls]) )
            entry = []
            entry.append( min(self.levels[cls]) )
            entry.append( self.means[cls] - e_j )
            entry.append( self.means[cls] + e_j )
            entry.append( max(self.levels[cls]) )
            stdDev1Intervals[cls] = entry;
        self.stdDev1Intervals = stdDev1Intervals
    
    def analyse(self, data):
        #TODO: complain if data set is empty!
        if len(data) < 5:
            return
        
        # add the real value to the correct bin
        for datum in data:
            self.levels[datum.x].append(datum.y)

        #TODO: Prune away empty levels
        levelsToPrune = filter(lambda lvl: len(self.levels[lvl]) == 0, self.levels)
        for lvlDel in levelsToPrune:
            del self.levels[lvlDel]
        
        #find the mean. Since bins are probably unbalanced
        # (we're crowdsourcing, after all, weight each bin)
        # by its size
        #while doing that, find column means just as well
        means = {}
        weights = {}
        mu = 0
        total = 0
        for level in self.levels:
            means[level] = sum(self.levels[level]) / float(len(self.levels[level]))
            weights[level] = len(self.levels[level])
            total += weights[level]
        for level in self.levels:
            weights[level] = float(weights[level]) / total
            mu = weights[level] * means[level]
        
        self.means = means
        self.find1StdDevIntervals()
        
        # We have to check that we have at least 1 more 
        # class in data to try to get this
        if len(self.levels) > 1:
            #Ok, we have column and grand means.
            # find bin alphas
            self.means = means
            alphas = {}
            for level in self.levels:
              alphas[level] = means[level] - mu
              
            # Next, find SSA, SSE
            SSA = 0
            SSE = 0
            
            for j in self.levels:
                r_j = len(self.levels[j])
                SSA += r_j*alphas[j]*alphas[j]
                for y_ij in self.levels[j]:
                    e_ij = y_ij - mu - alphas[j]
                    SSE += e_ij * e_ij
            # Now, we have SSA, SSE, compute MSA, MSE
            # Note that r computation is a bit sketchy: since we
            #   don't have the same number of observations for each
            #   label, we have to compute it as a weighted average of
            #   all classes, then round and make an integer to get
            #   an f-table value
            
            a = len(alphas)
            r = sum( map(lambda i: weights[i]*len(self.levels[i]), self.levels) )
            r = int(round(r))
            MSA = SSA / (a - 1)
            MSE = SSE / (a * (r - 1))
            F_value = MSA / MSE
            F_cmp = f_table_value(a-1, a*(r-1))
            if (F_value > F_cmp):
                # THIS IS THE CASE OF SIGNIFICANT RESULTS!
                pass
            else:
                # THIS MEANS OUR EXPERIMENT SHOWS NO CORRELATION
                pass
            # Now, perform the tests, etc
    
    def summary(self):
        return "TODO: Summany @ OneFactorAnalysis"
