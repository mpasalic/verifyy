# Create your views here.

from main.models import *
from main.conversion import parseTypeOrError

from main.statistics.common import Analysis, Regression
from main.statistics.linear_regression import LinearRegression
from main.statistics.one_factor import OneFactorAnalysis
from main.statistics.bayessian import SimpleBayessianAnalysis

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
    
    # NOTE: -Alex
    #   We don't need to run regression here, because we will load it
    #   in AJAX way from the page by GET data/...
    #
    
    params = {
        'exp': exp, 
        'request': request, 
        'user_data': data, 
        'subscription': sub,
        #'comments': [DiscussionMessage(experiment=exp,title="", message="Hello!") ] })
        'comments': comm,
        'x_choices': None,
        'y_choices': None
    }
    
    if exp.x_type == 'c':
        params['x_choices'] = ChoiceOptions.objects.filter(experiment=exp, var='x')
    if exp.y_type == 'c':
        params['y_choices'] = ChoiceOptions.objects.filter(experiment=exp, var='y')
    
    return render_to_response('experiment.html', params)


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
        
        xraw = request.POST['x'];
        yraw = request.POST['y'];
        x_enum = None
        y_enum = None
        
        # See what kind of experiment are we doing:
        
        if exp.x_type == 'c':
            x_enum_objs = ChoiceOptions.objects.filter(experiment=exp, var='x')
            x_enum = set()
            for obj in x_enum_objs:
                x_enum.add(obj.order)
        
        if exp.y_type == 'c':
            y_enum_objs = ChoiceOptions.objects.filter(experiment=exp, var='y')
            y_enum = set()
            for obj in y_enum_objs:
                y_enum.add(obj.order)
        
        try:
            x_val = parseTypeOrError(xraw, exp.x_type, x_enum)
            y_val = parseTypeOrError(yraw, exp.y_type, y_enum)
            
            data = Data(x = x_val, y = y_val, comments = request.POST['comments'], experiment = exp, user = request.user);
            data.save()
        
        except ValueError:
            return render_to_response('submiterror.html', {'exp': exp, 'message': submit_error(exp.x_name)})
        
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

REGRESSION_KIND         = 1
SINGLE_FACTOR_KIND      = 2
DISCRETE_OPT_KIND       = 3

def data(request, exp_id):
    exp = get_object_or_404(Experiment, pk=exp_id)
    
    #Possible experiment types:
    # exp.x_type/exp.y_type:
    #   Also note: time data and timeperiod data is also a bit different, but
    #              both are subclasses of real data.
    #       Everything except for 'c' pretty much stands for real-valued data
    #
    #   rr - real to real data, charts & regression analysis
    #   cr - choice to real - perform one-factor experiment analysis, draw candlestick charts
    #   cc - choice to choice - perform Bayesian analysis, draw column charts
    #   rc - FORBIDDEN, always should have X (factor) as a discrete variable in this case
    #   *t - FORBIDDEN, it does not make sense to analyze TIME as the dependent variable
    
    data = get_data(request, exp_id)
    analysis = Analysis()
    renderparams = {
        'exp': exp, 
        'data':data, 
        'request': request,
        #
        'regression': False,
        'onefactor': False,
        'discrete': False
    }
    kind = -1
    
    if exp.y_type == 't':
        raise KeyError("This kind of experiment should not exist!")
    
    if exp.x_type != 'c':
        if exp.y_type != 'c':
            kind = REGRESSION_KIND
            analysis = LinearRegression()
        else:
            raise KeyError("This kind of experiment should not exist!")
    else:
        # Fetch the possible values of X:
        xopts = ChoiceOptions.objects.filter(experiment=exp,var='x')
        xoptsDataForm = map(lambda opt: opt.order, xopts)
        xoptsDataMap = {}
        for xopt in xopts:
            xoptsDataMap[xopt.order] = xopt.option
        renderparams['x_mapping'] = xoptsDataMap
        
        if exp.y_type != 'c':
            kind = SINGLE_FACTOR_KIND
            analysis = OneFactorAnalysis(xoptsDataForm)
        else:
            # Fetch the possible values of Y:
            yopts = ChoiceOptions.objects.filter(experiment=exp,var='y')
            yoptsDataForm = map(lambda opt: opt.order, yopts)
            yoptsDataMap = {}
            for yopt in yopts:
                yoptsDataMap[yopt.order] = yopt.option
            renderparams['y_mapping'] = yoptsDataMap
            
            analysis = SimpleBayessianAnalysis(xoptsDataForm, yoptsDataForm)
            kind = DISCRETE_OPT_KIND
    #endif 
    
    try:
        analysis.analyse(data)
        
        if kind == REGRESSION_KIND:
            renderparams['regression'] = analysis
        elif kind == SINGLE_FACTOR_KIND:
            renderparams['onefactor'] = analysis
        elif kind == DISCRETE_OPT_KIND:
            renderparams['discrete'] = analysis
            
        # TODO: Re-add ZeroDivisionError
    except (RuntimeError, TypeError, NameError):
        #TODO: ALERT
        pass
    
    if kind == REGRESSION_KIND:
        # TODO: I think we shouldn't do it on our side
        #   move to the client?
        xmin = 0
        xmax = 0
        ymin = 0
        ymax = 0
        for item in data:
            if xmin > item.x:
                xmin = item.x
            if xmax < item.x:
                xmax = item.x
            if ymin > item.y:
                ymin = item.y
            if ymax < item.y:
                ymax = item.y
        renderparams['xmin'] = xmin
        renderparams['xmax'] = xmax
        renderparams['ymin'] = ymin
        renderparams['ymax'] = ymax
    elif kind == SINGLE_FACTOR_KIND:
        # Include candle parameters to draw here
        intervals = map(lambda bin: [bin] + analysis.stdDev1Intervals[bin], analysis.stdDev1Intervals)
        renderparams['x_intervals'] = intervals
    elif kind == DISCRETE_OPT_KIND:
        test = analysis.table
        renderparams['tally'] = analysis.table
    
    #   a = renderparams['regression']
    #b = a.slope
    #c = a.intercept
    #ass = 1/0
    return render_to_response('data.xml', renderparams, mimetype="application/xml")

	#xaxis = []
	#for i in range(10):
	#	xaxis.append( ((xmax - xmin)/10.0)*(i) + xmin )
	#	
	#regression = LinearRegression()
	#
	#try:
	#	regression.analyse(data)
	#except (ZeroDivisionError):
	#	regression = False


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

def create_new(request):
	return render_to_response('new_experiment.html', { 'request': request  })

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
        exp.x_type = request.POST['xtype']
        exp.y_type = request.POST['ytype']
        exp.user = request.user
        exp.vote = 0
        
        exp.save()
        
        # TODO: in options, check for unicodoce
        if exp.x_type == 'c':
            i = 0
            while ('choice_x_%d' % i) in request.POST:
                option = ChoiceOptions()
                option.option = request.POST[('choice_x_%d' % i)]
                if len(tokenize(option.option)) > 0:
                    option.order = i
                    option.experiment = exp
                    option.var = 'x'
                    option.save()
                i = i + 1
        
        if exp.y_type == 'c':
            i = 0
            while ('choice_y_%d' % i) in request.POST:
                option = ChoiceOptions()
                option.option = request.POST[('choice_y_%d' % i)]
                if len(tokenize(option.option)) > 0:
                    option.order = i
                    option.experiment = exp
                    option.var = 'y'
                    option.save()
                i = i + 1
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
                put_wall(at, "I just created an experiment called `%s` on VerifyY, come check it out!" % (exp.y_name + " with " + exp.x_name) )
    except (KeyError):
        return render_to_response('new_experiment.html', { 'error_message' : "Please fill out all fields",  'request': request  })
    
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
