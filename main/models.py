from django.db import models
from django.contrib.auth.models import User
from datetime import datetime 
from django.db.models.fields.related import ForeignKey

DATA_TYPES = (
    ('t', 'Date and Time'),
	('r', 'Real Number'),
	('c', 'Choice')
)

class Experiment(models.Model):
	x_name = models.CharField(max_length=256)
	x_type = models.CharField(max_length=1, choices=DATA_TYPES)
	x_units = models.CharField(max_length=256)
	
	y_name = models.CharField(max_length=256)
	y_type = models.CharField(max_length=1, choices=DATA_TYPES)
	y_units = models.CharField(max_length=256)
	
	description = models.TextField()
	created = models.DateTimeField(auto_now=True)
	user = models.ForeignKey(User)
	
	def votes(self):
		upvotes = self.vote_set.filter( vote=True).count()
		downvotes = self.vote_set.filter( vote=False).count()
		
		total = (upvotes - downvotes)
		return total
		
	votetotal = models.IntegerField(default=0)

	def __unicode__(self):
		return self.x_name + " with " + self.y_name

class FBAuth(models.Model):
	user = models.ForeignKey(User)
        code = models.TextField()
class FBAuth2(models.Model):
	user = models.ForeignKey(User)
        token = models.TextField()
		
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
	created = models.DateTimeField(auto_now=True, default=datetime.now())
	
class Vote(models.Model):
	user = models.ForeignKey(User)
	experiment = models.ForeignKey(Experiment)
	vote = models.BooleanField()
	created = models.DateTimeField(auto_now=True, default=datetime.now())
	
class Friend(models.Model):
	user = models.ForeignKey(User)
	friend = models.ForeignKey(User)
	created = models.DateTimeField(auto_now=True, default=datetime.now())

class Index(models.Model):
	word = models.CharField(max_length=256)
	doc = models.ForeignKey(Experiment)

	def __str__(self):
		return self.word + " => " + str(self.doc.id)

class ChoiceOptions(models.Model):
	option = models.CharField(max_length=256)
	order = models.IntegerField()
	var = models.CharField(max_length=1)
	experiment = models.ForeignKey(Experiment)

class Data(models.Model):
    x = models.FloatField()
    y = models.FloatField()
    # We don't really need that, choices are experiment-defined parameters
    #x_choice = models.ForeignKey(ChoiceOptions, null=True, blank=True, default=None)
    #y_choice = models.ForeignKey(ChoiceOptions, null=True, blank=True, default=None)
    comments = models.TextField()
    experiment = models.ForeignKey(Experiment)
    created = models.DateTimeField(auto_now=True, default=datetime.now())
    user = models.ForeignKey(User)
    
    def __unicode__(self):
        return self.x + ", " + self.y

