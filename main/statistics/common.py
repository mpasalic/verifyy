import inspect

class Analysis(object):    
	def summary(self):
		return "No analysis"
    
	def analyse(self, data):
		pass


class Regression(Analysis):
    def regress(self, x, y):
        pass
    
    def summary(self):
        return "No analysis"
    
    def analyse(self, data):
        x = []
        y = []
        for datum in data:
            x.append(datum.x)
            y.append(datum.y)
        self.regress(x, y)
        
    def fmtTerm(self, x):
        if x < 0:
            return "- %.2f" % abs(x)
        return "+ %.2f" % abs(x)
    
# RegressionPicker uses r^2 values to 
# pick the best regression
class RegressionPicker(Analysis):
    regressions = []
    
    def __init__(self, regressionList):
        super(RegressionPicker, self).__init__()
        self.regressions = regressionList
    
    def analyse(self, data):
        stealResultsFrom = None
        vals = []
        for regression in self.regressions:
            try:
                regression.analyse(data)
                if hasattr(regression, 'r_2'):
                    vals.append(regression.r_2)
                    if regression.r_2 > 0.7:
                        stealResultsFrom = regression
                        break
            except Exception as e:
                pass
        if None != stealResultsFrom:
            for name, thing in inspect.getmembers(stealResultsFrom):
                if not name.startswith('_'):
                    if not callable(thing):
                        setattr(self, name, thing)
            if hasattr(self, 'r_2'):
                self.summary = stealResultsFrom.summary
                
    
    