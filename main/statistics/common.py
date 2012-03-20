
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
    