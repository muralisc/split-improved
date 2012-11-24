from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.contrib.auth.models import User, Permission
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from projectApp1.forms import LoginCreateForm
from projectApp1.models import GroupForm, Membership, Group, Invite
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
    member_of = Membership.objects.filter(user=request.user)
    no_of_invites = Invite.objects.filter(to_user=request.user).filter(unread=True).count()
    # get invites count
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
    '''
    creates a group with one member; the creator as admin
    '''
    if request.method == 'POST':
        form = GroupForm(request.POST)
        if form.is_valid():
            groupRow = form.save(commit=False)
            groupRow.save()
            Membership.objects.create(
                                    group=groupRow,
                                    user=request.user,
                                    administrator=True,
                                    positions='creator',
                                    amount_in_pool=0
                                    )
            groupRow.invite(request.user, form.cleaned_data['members'])
        else:
            pass
    else:
        pass
    return redirect('/group/{0}/'.format(groupRow.id))


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


@login_required(login_url='/login/')
def changeInvite(request, accept_decline, row_id):
    '''
    creates membership from an invite
    delets an invite
    '''
    invite = Invite.objects.get(pk=row_id)
    if invite.to_user.id == request.user.id:
        if accept_decline == 'accept':
            # membership alredy exixt problem[alredy taken care while making invite]
            Membership.objects.create(
                                    group=invite.group,
                                    user=invite.to_user,
                                    administrator=False,
                                    positions='',
                                    amount_in_pool=0
                                    )
            invite.delete()
            return redirect('/home/')
        elif accept_decline == 'decline':
            invite.delete()
            return redirect('/home/')
        else:
            raise Http404
    else:
        raise Http404


@login_required(login_url='/login/')
def showInvites(request):
    all_invites = Invite.objects.filter(to_user=request.user).filter(unread=True)
    return render_to_response('allInvites.html', locals(), context_instance=RequestContext(request))
