# Create your views here.
from main.models import Experiment, Subscription, Data

from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.shortcuts import redirect
from django.contrib.auth.models import User
from django.contrib import auth
from exceptions import ValueError
from django.db.models import Q

def index(request):

	list = Experiment.objects.all().order_by('-created')[:5]
	return render_to_response('index.html', { 'request': request, 'list':list })

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
			user = User.objects.create_user(request.POST['username'], request.POST['email'], request.POST['password'])
			user.save();
		except (KeyError):
			return render_to_response('register.html', { 'error_message' : "Please fill out all fields",  'request': request  })
		else:
			return render_to_response('login.html', { 'info_message' : "Succesfully registered user", 'request': request  })

def experiment(request, exp_id):
	exp = get_object_or_404(Experiment, pk=exp_id)
	data = Data.objects.filter(experiment = exp, user = request.user)
	
	try:
		sub = Subscription.objects.get(experiment = exp, user = request.user)
	except (Subscription.DoesNotExist):
		sub = False
	
	return render_to_response('experiment.html', {'exp': exp, 'request': request, 'user_data': data, 'subscription': sub})

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

def data(request, exp_id):
	exp = get_object_or_404(Experiment, pk=exp_id)
	return render_to_response('data.xml', {'exp': exp, 'request': request }, mimetype="application/xml")

def create_experiment(request):
	if not request.user.is_authenticated():
		return login(request)

	exp = Experiment()
	try:
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
	q = ""
	if 'q' in request.GET:
		q = request.GET['q']
		found_entries = Experiment.objects.all().filter( y_name=q )
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
	