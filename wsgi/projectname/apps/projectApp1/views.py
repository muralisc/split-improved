from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.contrib.auth.models import User
from projectApp1.forms import LoginCreateForm


def createUser(request):
    if request.method == 'POST':
        form = LoginCreateForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            username = email
            password = form.cleaned_data['password']
            user = User.objects.create_user(username, email, password)
            #myuser.user_permissions.add(permission, permission,)
            user.save()
            newUserCreated = True
    else:
        form = LoginCreateForm()
    return render_to_response('loginCreate.html', locals(), context_instance=RequestContext(request))


#def login(request):
#    return render_to_response('login.html', locals(), context_instance=RequestContext(request))
