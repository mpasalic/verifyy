# Create your views here.

from main.models import *
from main.conversion import parseTypeOrError, convertTimeByFolding, TIME_FOLDING, REGRESSION_PREFERENCE
from main.searchapi import addToIndex, search1

from main.statistics.common import Analysis, Regression, RegressionPicker
from main.statistics.linear_regression import LinearRegression
from main.statistics.poly_2nd import Poly2OrderRegression
from main.statistics.one_factor import OneFactorAnalysis
from main.statistics.b_spline_regression import BSplineRegression
from main.statistics.chi_analysis import ChiSquareTest

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
import fb

def authCheck(request):
    authed = not isinstance(request.user,AnonymousUser)
    return render_to_response('auth.html', {'authed': authed, 'user': request.user} )

def msg(request):
    at = fb.get_auth_token(request)
    fb.put_wall(at, "I just created an experiment on VerifyY, come check it out!")

    #return render_to_response('hello.html', {'code': get_auth_token(request)})
    return render_to_response('hello.html', {'code': get_name(at)})

def create_user(userName, name, password, email):
        existingUser = User.objects.filter(username = userName)
        if len(existingUser) == 0:
                user = User.objects.create_user(userName, email, password)
                user.save();

                UserProfile(user=user, name=name).save()
                return True
        else:
                return False

def index(request):
	authed = not isinstance(request.user,AnonymousUser)
	if 'code' in request.GET and not authed:
                code = request.GET['code']
                token = fb.get_token_from_code(code)
                user = "fb_" + fb.get_profile(token)["id"]
                password = "208phoeu092uent"
                create_user(user, fb.get_profile(token)["name"], 
                            password, "foo@suremail.info")
		user = auth.authenticate(username=user, password=password)
                auth.login(request, user)
                fb.save_code(user, code)
                return redirect('/');

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
			if not create_user(userName, 
                                           userName,
                                           request.POST['password'],
                                           request.POST['email']):

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
        except ValueError, err:
            #return render_to_response('debugger_response.xml', {'debug': {'1':err}})
            return render_to_response('submiterror.html', {'exp': exp, 'message': submit_error(exp.x_name)})
    
    #return render_to_response('debugger_response.xml', {'debug': {'1':err}})
    return redirect("/view/%d/" % int(exp_id));
	
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
    #   cc - choice to choice - perform ChiSquareTest analysis, draw column charts
    #   rc - FORBIDDEN, always should have X (factor) as a discrete variable in this case
    #   *t - FORBIDDEN, it does not make sense to analyze TIME as the dependent variable
    
    data = get_data(request, exp_id)
    
    time_fold = TIME_FOLDING.NO_FOLD
    regression_type = REGRESSION_PREFERENCE.NONE
    
    if 'time_fold' in request.GET:
        time_fold = request.GET['time_fold']
        time_fold = TIME_FOLDING().foldingValueOf(time_fold)
    if 'regression_type' in request.GET:
        regression_type = request.GET['regression_type']
        regression_type = REGRESSION_PREFERENCE().enumValueOf(regression_type)
        
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
            if exp.x_type == 't':
                convertTimeByFolding(data, time_fold)
                renderparams['timefold'] = TIME_FOLDING().strValueOf(time_fold)
            kind = REGRESSION_KIND
            regressions = {
                REGRESSION_PREFERENCE.LINEAR: LinearRegression(), 
                REGRESSION_PREFERENCE.SECOND_POLY:Poly2OrderRegression(), 
                REGRESSION_PREFERENCE.B_SPLINE:BSplineRegression()
            }
            if (regression_type == REGRESSION_PREFERENCE.NONE):
                analysis = RegressionPicker(map(lambda x: regressions[x], regressions))
            else:
                analysis = regressions[regression_type]
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
            
            analysis = ChiSquareTest(xoptsDataForm, yoptsDataForm)
            kind = DISCRETE_OPT_KIND
    #endif 
    
    #try:
    analysis.analyse(data)
    
    if kind == REGRESSION_KIND:
        renderparams['regression'] = analysis
    elif kind == SINGLE_FACTOR_KIND:
        renderparams['onefactor'] = analysis
    elif kind == DISCRETE_OPT_KIND:
        renderparams['discrete'] = analysis
            
        # TODO: Re-add ZeroDivisionError
    #except (RuntimeError, TypeError, NameError):
        #TODO: ALERT
    #    pass
    
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
        renderparams['ymin'] = analysis.ymin
        renderparams['ymax'] = analysis.ymax
        renderparams['x_mean_effect'] = analysis.x_mean_effect
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
    errmsg = ["Please fill out all fields"]
    exp = Experiment()
    choicesX = []
    choicesY = []
    try:
        exp.x_name = request.POST['x']
        exp.y_name = request.POST['y']
        exp.description = request.POST['desc']
        exp.x_units = request.POST['xunits']
        exp.y_units = request.POST['yunits']
        exp.x_type = request.POST['xtype']
        exp.y_type = request.POST['ytype']
        exp.user = request.user
        exp.vote = 0
		
        def process_choices(var, vartype, errmsg):
            if vartype != 'c':
                return []
            options = []
            i = 0
            while ('choice_%s_%d' % (var, i)) in request.POST:
                option = ChoiceOptions()
                option.option = request.POST[('choice_%s_%d' % (var, i))].strip()
                if len(option.option) > 0:
                    option.order = i
                    option.var = var
                    options.append(option)
                i = i + 1
            if len(options) < 2:
                errmsg[0] = "You must specify at least 2 different states for %s" % var
                raise KeyError(errmsg)
            return options
        
        choicesX = process_choices('x', exp.x_type, errmsg)
        choicesY = process_choices('y', exp.y_type, errmsg)
		
        if len(exp.x_name) < 3:
            errmsg[0] = "The x variable must be at least 3 letters."
            raise KeyError(errmsg)
        if len(exp.y_name) < 3:
            errmsg[0] = "The y variable must be at least 3 letters."
            raise KeyError(errmsg)
        if len(exp.description) == 0:
            errmsg[0] = "You must provide a description."
            raise KeyError(errmsg)
        
        # If we've made it this far, we can save everything now
        exp.save()
        
        for option in choicesX:
            option.experiment = exp
            option.save()
        for option in choicesY:
            option.experiment = exp
            option.save()
        
        addToIndex(exp)
        
        at = fb.get_auth_token(request)
        fb.put_wall(at, "I just created an experiment called `%s` on VerifyY, come check it out!" % (exp.y_name + " with " + exp.x_name) )
    except (KeyError):
        return render_to_response('new_experiment.html', {'error_message':errmsg[0], 'request':request, 'exp':exp,
                                                          'choicesX':choicesX, 'choicesY':choicesY})
	
    
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
		found_entries = search1(q)
	else:
		found_entries = ''
	return render_to_response('search.html', { 'search': q, 'list': found_entries, 'request': request })
	
def searchXml(request):
    if 'q' in request.POST:
        q = request.POST['q']
        found_entries = search1(q)
        return render_to_response('search.xml', {'search': q, 'list': found_entries}, mimetype="application/xml")
    else:
        return HttpResponseBadRequest('<search />')
	
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
