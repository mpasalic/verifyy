# Create your views here.
from django.http import HttpResponse
from django.shortcuts import render_to_response

def index(request):
    return render_to_response('index.html')
def new_experiment(request):
    return render_to_response('new_experiment.html')
def create_experiment(request):
    return render_to_response('experiment.html');

