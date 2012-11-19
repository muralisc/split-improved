import json
from django.shortcuts import render_to_response, redirect, HttpResponse
from django.template import RequestContext
from django.contrib.auth.models import User, Permission
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from projectApp1.forms import LoginCreateForm
from projectApp1.models import TransactionForm, Category
from django.utils.safestring import SafeString


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
            pass
            # form is invalid erros auto set
    else:
        pass
        # redict to login
    return redirect('/login/')


def siteLogin(request):
    if request.user.is_authenticated():
        return redirect('/home/')
    if request.method == 'POST':
        form = LoginCreateForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(username=email, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    return redirect('/home/')
                    #return redirect('http://google.com')
                    # redirect to success page
                else:
                    pass
                    # redirect ot 'dissabled account'
            else:
                wrongUsernameOrPassword = True
        else:
            pass
            # form is invalid erros auto set
    else:
        form = LoginCreateForm()
    return render_to_response('loginCreate.html', locals(), context_instance=RequestContext(request))


@login_required(login_url='/login/')
def home(request):
    return render_to_response('home.html', locals(), context_instance=RequestContext(request))


@login_required(login_url='/login/')
def enableDissablePermissions(request, codename, enableDissable):
    try:
        perm = Permission.objects.get(codename=codename)
        usr = request.user
        if enableDissable == 'dissable':
            usr.user_permissions.remove(perm)
            usr.save()
        else:
            usr.user_permissions.add(perm)
            usr.save()
        return redirect('/settings/')
    except Permission.DoesNotExist:
        # log error
        return redirect('/settings/')


@login_required(login_url='/login/')
def makeTransaction(request):
    form = TransactionForm()
    users_in_grp = [{'username': usr.username, 'id': usr.id, 'checked': False} for usr in User.objects.all()]
    category_user = [{'name': i.name, 'id': i.id} for i in Category.objects.all()]
    response_json = dict()
    response_json['users_in_grp'] = SafeString(json.dumps(users_in_grp))
    response_json['category_user'] = SafeString(json.dumps(category_user))
    return render_to_response('makeTransaction.html', locals(), context_instance=RequestContext(request))
