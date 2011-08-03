from django.db import models
from django.contrib.auth.models import User
from django.db.models.fields.related import ForeignKey


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
	
	def votes(self):
		upvotes = self.vote_set.filter( vote=True).count()
		downvotes = self.vote_set.filter( vote=False).count()
		
		total = (upvotes - downvotes)
		return total
		
	def __unicode__(self):
		return self.x_name + " with " + self.y_name
		
class DiscussionMessage(models.Model):
	experiment = models.ForeignKey(Experiment)
	user = models.ForeignKey(User)
	#order by tree branch / timestamp allows to get the tree
	tstamp = models.DateTimeField(auto_now=True)
	branch = models.IntegerField()
	title = models.CharField(max_length=256)
	message = models.TextField()
	
	
class Subscription(models.Model):
	user = models.ForeignKey(User)
	experiment = models.ForeignKey(Experiment)
	
class Vote(models.Model):
	user = models.ForeignKey(User)
	experiment = models.ForeignKey(Experiment)
	vote = models.BooleanField()

class Index(models.Model):
        word = models.CharField(max_length=256)
	doc = models.ForeignKey(Experiment)

	def __str__(self):
		return self.word + " => " + str(self.doc.id)

class Data(models.Model):
	x = models.IntegerField()
	y = models.IntegerField()
	comments = models.TextField()
	experiment = models.ForeignKey(Experiment)
	created = models.DateTimeField(auto_now=True)
	user = models.ForeignKey(User)

	def __unicode__(self):
		return self.x + ", " + self.y
