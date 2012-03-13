# Create your views here.

from main.models import *
from main.analysis import Regression, LinearRegression

from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.shortcuts import redirect
from django.contrib.auth.models import User, AnonymousUser
from django.contrib import auth
from exceptions import ValueError
from django.db.models import Avg, Max, Min, Count, Q
import urllib2
import re
import main.facebook as fb

def authCheck(request):
    authed = not isinstance(request.user,AnonymousUser)
    return render_to_response('auth.html', {'authed': authed, 'user': request.user} )

def get_auth_token(request):
    res = FBAuth.objects.filter(user=request.user)
    if not res: return None
    code = res[0].code

    r = urllib2.urlopen("https://graph.facebook.com/oauth/access_token?client_id=205425319498174&redirect_uri=http://localhost:8000/&client_secret=1a5aa67a3a7f8bbe40422a8d01445e82&code=%s" % code).read()
    return r.split('=')[1]

def get_cached_token(request):
    authed = not isinstance(request.user,AnonymousUser)
    if not authed: return None
    res = list(FBAuth2.objects.filter(user=request.user))
    if not res: return None
    return res[-1].token

def get_name(at):
    if not at: return ""
    g = fb.GraphAPI(access_token = at )
    me = g.get_object('me')
    return me['first_name'] + ' ' + me['last_name']

def put_wall(at, msg):
    if not at: return None
    g = fb.GraphAPI(access_token = at)
    g.put_object("me", "feed",
                message=msg,
               name= 'VerifyY',
               picture= 'http://myfriendfactory.appspot.com/static/images/wall.png',
               link= 'http://www.verifyy.com',
               actions= [
                    {
                       "name": "View Experiment",
                       "link": "http://www.verifyy.com/"
                    }])
          
    


def msg(request):
    at = get_auth_token(request)
    put_wall(at, "I just created an experiment on VerifyY, come check it out!")

    #return render_to_response('hello.html', {'code': get_auth_token(request)})
    return render_to_response('hello.html', {'code': get_name(at)})

def index(request):
	authed = not isinstance(request.user,AnonymousUser)
	if 'code' in request.GET and authed:
		fba = FBAuth(code = request.GET['code'], user = request.user)
		fba.save()

		at = get_auth_token(request)
		fba = FBAuth2(token = at, user = request.user)
		fba.save()

	list = Experiment.objects.all().order_by('-votetotal')[:5]
	return render_to_response('frontpage.html', {# 'fullname': get_name(at), 
        'request': request, 'list':list })

def login(request):
	if (request.method == 'GET'):
		return render_to_response('login.html', { 'request': request })
	elif (request.method == 'POST'):
		user = auth.authenticate(username=request.POST['username'], password=request.POST['password'])
		if user is not None:
			if user.is_active:
				auth.login(request, user)
				return redirect('/');
			else:
				return render_to_response('login.html', { 'error_message' : "Account is disabled.", 'request': request  })
		else:
			return render_to_response('login.html', { 'error_message' : "Invalid username or password.",  'request': request })

def logout(request):
	auth.logout(request)
	return render_to_response('login.html', { 'request': request, 'info_message': "Succesfully logged out" })

def register(request):
	if (request.method == 'GET'): 
		return render_to_response('register.html', { 'request': request })
	elif (request.method == 'POST'):
		try:
			userName = request.POST['username']
			existingUser = User.objects.filter(username = userName)
			if len(existingUser) == 0:
				user = User.objects.create_user(userName, request.POST['email'], request.POST['password'])
				user.save();
			else:
				return render_to_response('register.html', { 'error_message' : "Username is taken",  'request': request  })
		except (KeyError):
			return render_to_response('register.html', { 'error_message' : "Please fill out all fields",  'request': request  })
		else:
			return render_to_response('login.html', { 'info_message' : "Succesfully registered user", 'request': request  })

def experiment(request, exp_id):
	exp = get_object_or_404(Experiment, pk=exp_id)
	data = Data.objects.filter(experiment = exp, user = request.user)
	comm = DiscussionMessage.objects.filter(experiment = exp).order_by('timestamp').order_by('branch')[:50]
	
	sub = False
	try:
		if request.user.is_authenticated():
			sub = Subscription.objects.get(experiment = exp, user = request.user)
	except (Subscription.DoesNotExist):
		sub = False
		
	vote = exp.votes()
	
	regression = LinearRegression()
	regression.analyse(exp.data_set.all())

	
	return render_to_response('experiment.html', 
							{'exp': exp, 
							'request': request, 
							'user_data': data, 
							'subscription': sub,
							#'comments': [DiscussionMessage(experiment=exp,title="", message="Hello!") ] })
							'comments': comm})


def postcomm(request, exp_id):
	authed = not isinstance(request.user,AnonymousUser)
	if(request.method == 'POST' and authed):		
		exp = get_object_or_404(Experiment, pk = exp_id)
		msgTitle = request.POST['title']
		msgBody = request.POST['message']
		
		if msgBody != "" :
			msg = DiscussionMessage(experiment = exp, user=request.user, title=msgTitle, message=msgBody)
			msg.branch = 0
			msg.save()
	return redirect("/view/%d/" % (exp.id));

def submit_error(var_name):
	return "'%s' must be a whole number." % var_name;
	
def submit(request, exp_id):
	if(request.method == 'POST'):
		exp = get_object_or_404(Experiment, pk=exp_id)
		try:
			x_val = int(request.POST['x'])
		except ValueError:
			return render_to_response('submiterror.html', {'exp': exp, 'message': submit_error(exp.x_name)})
		try:
			y_val = int(request.POST['y'])
		except ValueError:
			return render_to_response('submiterror.html', {'exp': exp, 'message': submit_error(exp.y_name)})
			
		data = Data(x = x_val, y = y_val, comments = request.POST['comments'], experiment = exp, user = request.user);
		data.save()
	return redirect("/view/%d/" % (exp.id));
	
def new_experiment(request):
    return render_to_response('new_experiment.html', {'request': request})

def get_data(request, exp_id):
	exp = get_object_or_404(Experiment, pk=exp_id)

	if 'filter' in request.GET:
		filter = request.GET['filter']

		if filter == '1':
			return Data.objects.all().filter( experiment=exp, user=request.user )
		elif filter == '2':
			friends = Friend.objects.all().filter( user=request.user)
			data = []
			for datapoint in Data.objects.all().filter( experiment=exp, user=request.user ):
				data.append(datapoint)
				
			for friend in friends:
				for datapoint in Data.objects.all().filter( experiment=exp, user=friend.friend ):
					data.append(datapoint)
					
			return data
			
	return Data.objects.all().filter( experiment=exp )
	

def data(request, exp_id):
	exp = get_object_or_404(Experiment, pk=exp_id)
	
	xmin = 0
	xmax = 0
	ymin = 0
	ymax = 0
	
	data = get_data(request, exp_id)
	
	for item in data:
		if xmin > item.x:
			xmin = item.x
		if xmax < item.x:
			xmax = item.x
		if ymin > item.y:
			ymin = item.y
		if ymax < item.y:
			ymax = item.y
			
	xaxis = []
	
	for i in range(10):
		xaxis.append( ((xmax - xmin)/10.0)*(i) + xmin )
		
	regression = LinearRegression()
	
	try:
		regression.analyse(data)
	except (ZeroDivisionError):
		regression = False
	
	return render_to_response('data.xml', {'xaxis': xaxis, 'xmin': xmin, 'xmax': xmax, 'ymin': ymin, 'ymax': ymax,
		'exp': exp, 'data':data, 'regression': regression, 'request': request }, mimetype="application/xml")

def edit(request, exp_id):
	exp = get_object_or_404(Experiment, pk=exp_id)
	if request.user == exp.user or request.user.is_superuser:
		if request.method == 'GET':
			return render_to_response('edit.html', {'exp': exp, 'request': request })
		elif request.method == 'POST':
			exp.x_name = request.POST['x']
			exp.y_name = request.POST['y']
			exp.description = request.POST['desc']
			exp.x_units = request.POST['xunits']
			exp.y_units = request.POST['yunits']
			exp.x_control = request.POST['xdesc']
			exp.y_control = request.POST['ydesc']
			exp.save()
			return experiment(request, exp_id)
			
	else:
		return experiment(request, exp_id)
	
	

def tokenize(c):
    splitter = re.compile(r'\W+')
    return map(unicode.lower, splitter.split(c))

def create_experiment(request):
	if not request.user.is_authenticated():
		return login(request)

	try:
                exp = Experiment()
		exp.x_name = request.POST['x']
		exp.y_name = request.POST['y']
		exp.description = request.POST['desc']
		exp.x_units = request.POST['xunits']
		exp.y_units = request.POST['yunits']
		exp.x_control = request.POST['xdesc']
		exp.y_control = request.POST['ydesc']
		exp.user = request.user
		exp.vote = 0

	except (KeyError):
		return render_to_response('new_experiment.html', { 'error_message' : "Please fill out all fields",  'request': request  })
	else:
		exp.save()

                def index_contents(c):
                    for w in tokenize(c):
                        ind = Index()
                        ind.doc = exp
                        ind.word = w
                        ind.save()
                index_contents(exp.x_name)
                index_contents(exp.y_name)
                index_contents(exp.description)

                at = get_auth_token(request)
                put_wall(at, "I just created an experiment called `%s` on VerifyY, come check it out!"
                     % (exp.y_name + " with " + exp.x_name) )

		return redirect("/view/%d/" % (exp.id))
		
def join(request, exp_id):
	exp = get_object_or_404(Experiment, pk=exp_id)

	try:
		subscription = Subscription.objects.get(experiment=exp, user=request.user)
	except (Subscription.DoesNotExist):
		subscription = Subscription(experiment=exp, user=request.user)
		subscription.save()

	return redirect("/view/%d/" % (exp.id))


def unjoin(request, exp_id):
	exp = get_object_or_404(Experiment, pk=exp_id)
	subscription = get_object_or_404(Subscription, experiment=exp, user=request.user)

	subscription.delete()

	return redirect("/view/%d/" % (exp.id))

def search(request):
	# TODO: multiple search pages!
	q = ""
	if 'q' in request.GET:
		q = request.GET['q']

                indexes = set()
                for w in tokenize(q):
                    indexes.update(map(lambda r: r.doc, Index.objects.all().filter(word=w)))

		found_entries = indexes
	else:
		found_entries = ''
	return render_to_response('search.html', { 'search': q, 'list': found_entries, 'request': request })
	
def user(request, username):
	user = get_object_or_404(User, username=username)
	subs = Subscription.objects.all().filter( user=user )
	data = Data.objects.all().filter( user=user )

	exp = []
	for sub in subs:
		exp.append(sub.experiment)
	return render_to_response('user.html', { 'user': user, 'list': exp, 'data': data, 'request': request })


def friends(request):
	if not request.user.is_authenticated():
		return login(request)
	else:
		if 'add' in request.GET:
			addfriend(request, request.GET['add'])
		elif 'remove' in request.GET:
			removefriend(request, request.GET['remove'])
		
		return render_to_response('friends.html', {'request': request, 'list': Friend.objects.all().filter(user=request.user) })
		
def addfriend(request, username):
	user = get_object_or_404(User, username=username)
	if request.user.username == user.username:
		return
	
	try:
		friend = Friend.objects.get(user=request.user, friend=user)
	except (Friend.DoesNotExist):
		friend = Friend(user=request.user, friend=user)
		friend.save()
	
	return
		
def removefriend(request, username):

	user = get_object_or_404(User, username=username)
	friend = get_object_or_404(Friend, user=request.user, friend=user)
	friend.delete()
	
	return

def upvote(request, exp_id):
	return vote(request, exp_id, True)
def downvote(request, exp_id):
	return vote(request, exp_id, False)

def vote(request, exp_id, voting):
	user = request.user
	
	if not user.is_authenticated():
		return login(request)
	
	exp = get_object_or_404(Experiment, pk=exp_id)
	try:
		vote = Vote.objects.get( user=user, experiment=exp )
		vote.vote = voting
		vote.save()
	except (Vote.DoesNotExist):
		vote = Vote(user=user, experiment=exp, vote=voting)
		vote.save()
	
	upvotes = Vote.objects.all().filter( experiment=exp, vote=True).count()
	downvotes = Vote.objects.all().filter( experiment=exp, vote=False).count()
	total = upvotes - downvotes
	exp.votetotal = total
	exp.save()
	
	return render_to_response('experiment.xml', { 'upvotes': upvotes, 'downvotes': downvotes, 'total': total,'exp': exp, 'request': request }, mimetype="application/xml")
