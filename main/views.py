# Create your views here.
from main.models import Experiment

from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.shortcuts import render_to_response

def index(request):
    return render_to_response('index.html')

def experiment(request, exp_id):	
#	exp = get_object_or_404(Experiment, pk=exp_id)
	return render_to_response('experiment.html', {'exp_id': exp_id})

def new_experiment(request):
    return render_to_response('new_experiment.html')

def create_experiment(request):
    return render_to_response('experiment.html');

