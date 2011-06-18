from django.db import models
from django.contrib.auth.models import User

class Experiment(models.Model):
	x_name = models.CharField(max_length=256)
	y_name = models.CharField(max_length=256)
	description = models.TextField()
	x_units = models.CharField(max_length=256)
	x_control = models.TextField()
	y_units = models.CharField(max_length=256)
	y_control = models.TextField()
	created = models.DateTimeField(auto_now=True)
	user = models.ForeignKey(User)
	vote = models.IntegerField()
	
	def __unicode__(self):
		return self.x_name + " with " + self.y_name
		
class Subscription(models.Model):
	user = models.ForeignKey(User)
	experiment = models.ForeignKey(Experiment)
	

class Data(models.Model):
	x = models.IntegerField()
	y = models.IntegerField()
	comments = models.TextField()
	experiment = models.ForeignKey(Experiment)
	created = models.DateTimeField(auto_now=True)
	user = models.ForeignKey(User)

	def __unicode__(self):
		return self.x + ", " + self.y