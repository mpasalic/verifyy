from django.db import models

class Experiment(models.Model):
	x_name = models.CharField(max_length=256)
	y_name = models.CharField(max_length=256)
	description = models.TextField()
	x_units = models.CharField(max_length=256)
	x_control = models.TextField()
	y_units = models.CharField(max_length=256)
	y_control = models.TextField()
	def __unicode__(self):
		return self.x_name + " with " + self.y_name

class Data(models.Model):
	x = models.IntegerField()
	y = models.IntegerField()
	comments = models.TextField()
	experiment = models.ForeignKey(Experiment)
	
	def __unicode__(self):
		return self.x + ", " + self.y