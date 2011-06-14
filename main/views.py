# Create your views here.
from main.models import Experiment

from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.shortcuts import redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login

def index(request):
    return render_to_response('index.html')

def login(request):
	if (request.method == 'GET'):
		return render_to_response('login.html')
	elif (request.method == 'POST'):
		user = authenticate(username=request.POST['username'], password=request.POST['password'])
		if user is not None:
			if user.is_active:
				auth.login(request, user)
				return redirect('/');
			else:
				return render_to_response('login.html', { 'error_message' : "Account is disabled." })
		else:
			return render_to_response('login.html', { 'error_message' : "Invalid username or password." })


def register(request):
	if (request.method == 'GET'): 
		return render_to_response('register.html')
	elif (request.method == 'POST'):
		try:
			user = User.objects.create_user(request.POST['username'], request.POST['email'], request.POST['password'])
			user.save();
		except (KeyError):
			return render_to_response('register.html', { 'error_message' : "Please fill out all fields" })
		else:
			return render_to_response('login.html', { 'info_message' : "Succesfully registered user" })

def experiment(request, exp_id):	
	exp = get_object_or_404(Experiment, pk=exp_id)
	return render_to_response('experiment.html', {'exp': exp})

def new_experiment(request):
    return render_to_response('new_experiment.html')

def data(request, exp_id):
	exp = get_object_or_404(Experiment, pk=exp_id)
	return render_to_response('data.xml', {'exp': exp}, mimetype="application/xml")

def create_experiment(request):
	exp = Experiment()
	try:
		exp.x_name = request.POST['x']
		exp.y_name = request.POST['y']
		exp.description = request.POST['desc']
		exp.x_units = request.POST['xunits']
		exp.y_units = request.POST['yunits']
		exp.x_control = request.POST['xdesc']
		exp.y_control = request.POST['ydesc']
		
	except (KeyError):
		return render_to_response('new_experiment.html', { 'error_message' : "Please fill out all fields" })
	else:
		exp.save()
		return redirect("/view/%d/" % (exp.id));
