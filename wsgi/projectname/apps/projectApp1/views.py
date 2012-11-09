# Django imports
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext

def login(request):
    return render_to_response('login.html', locals(), context_instance=RequestContext(request))
