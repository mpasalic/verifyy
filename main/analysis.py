from main.models import Data
from stats import linregress

class Regression(object):
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

class LinearRegression(Regression):
	slope = 0.0
	intercept = 0.0
	ttProb = 0.0
	r = 0.0
	points = 0
	
	def regress(self, x, y):
		self.points = len(x)
		if len(x) >= 2:
			self.slope, self.intercept, self.r, self.ttProb, sterr = linregress(x, y)
		
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
