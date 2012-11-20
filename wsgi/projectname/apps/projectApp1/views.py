import json
from django.shortcuts import render_to_response, redirect, HttpResponse
from django.template import RequestContext
from django.contrib.auth.models import User, Permission
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from projectApp1.forms import LoginCreateForm
from projectApp1.models import GroupForm, Membership, Group
from django.http import Http404


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
    form = GroupForm()
    members = Membership.objects.filter(user=request.user)
    return render_to_response('home.html', locals(), context_instance=RequestContext(request))


@login_required(login_url='/login/')
def enableDissablePermissions(request, codename, enableDissable):
    try:
        perm = Permission.objects.get(codename=codename)
        user = request.user
        if enableDissable == 'dissable':
            user.user_permissions.remove(perm)
            user.save()
        else:
            user.user_permissions.add(perm)
            user.save()
        return redirect('/settings/')
    except Permission.DoesNotExist:
        # log error
        return redirect('/settings/')


@login_required(login_url='/login/')
def createGroup(request):
    if request.method == 'POST':
        form = GroupForm(request.POST)
        if form.is_valid():
            groupRow = form.save(commit=False)
            groupRow.save()
            Membership.objects.create(
                                    group=groupRow,
                                    user=request.user,
                                    administrator=True,
                                    positions='',
                                    amount_in_pool=0
                                    )
            for member in form.cleaned_data['members']:
                Membership.objects.create(
                                        group=groupRow,
                                        user=member,
                                        administrator=False,
                                        positions='',
                                        amount_in_pool=0
                                        )
        else:
            pass
    else:
        pass
    return redirect('/settings/')


@login_required(login_url='/login/')
def groupHome(request, gid):
    try:
        group = Group.objects.get(id=gid)
    except Group.DoesNotExist:
        # log error 404
        raise Http404
    members = Membership.objects.filter(group=group)
    return render_to_response('groupHome.html', locals(), context_instance=RequestContext(request))


@login_required(login_url='/login/')
def settings(request):
    pass
    return render_to_response('userSettings.html', locals(), context_instance=RequestContext(request))
