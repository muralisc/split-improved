import simplejson
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.contrib.auth.models import User, Permission
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from projectApp1.forms import LoginCreateForm
from projectApp1.models import GroupForm, Membership, Group, Invite
from django.http import Http404, HttpResponse
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
    return render_to_response('loginCreate.html', locals(), context_instance=RequestContext(request))


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
                    request.session['memberships'] = Membership.objects.filter(user=request.user).filter(group__deleted=False)
                    if 'next_url' in request.session:
                        return redirect(request.session['next_url'])
                    else:
                        return redirect('/home/')
                    # return redirect('http://google.com')
                    # redirect to success page
                else:
                    pass
                    # redirect ot 'dissabled account'
            else:
                wrongUsernameOrPassword = True
        else:
            pass
            # form is invalid erros auto set
    elif 'next' in request.GET:
        request.session['next_url'] = request.GET['next']
    form = LoginCreateForm()
    return render_to_response('loginCreate.html', locals(), context_instance=RequestContext(request))


@login_required(login_url='/login/')
def home(request):
    form = GroupForm()
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
            groupRow.privacy = ''
            groupRow.deleted = False
            groupRow.save()
            Membership.objects.create(
                                    group=groupRow,
                                    user=request.user,
                                    administrator=True,
                                    positions='creator',
                                    amount_in_pool=0
                                    )
            users_invited = [User.objects.get(pk=id) for id in request.POST['members'].split(',')]
            groupRow.invite(request.user, users_invited)
        else:
            pass
    else:
        pass
    return redirect('/group/{0}/'.format(groupRow.id))


@login_required(login_url='/login/')
def groupHome(request, gid):
    try:
        group = Group.objects.get(id=gid, deleted=False)
    except Group.DoesNotExist:
        # log error 404
        raise Http404
    members = Membership.objects.filter(group=group)
    invites = Invite.objects.filter(group=group)
    return render_to_response('groupHome.html', locals(), context_instance=RequestContext(request))


@login_required(login_url='/login/')
def settings(request):
    pass
    return render_to_response('userSettings.html', locals(), context_instance=RequestContext(request))


@login_required(login_url='/login/')
def changeInvite(request, accept_decline, row_id):
    '''
    creates membership from an invite
    deletes an invite
    '''
    invite = Invite.objects.get(pk=row_id)
    if invite.to_user.id == request.user.id:
        if accept_decline == 'accept':
            # membership alredy exixt problem[alredy taken care while making invite]
            if not Membership.objects.filter(group=invite.group).filter(user=invite.to_user).exists():
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


@login_required(login_url='/login/')
def getJSONusers(request):
    users_in_grp = [{'name': usr['username'], 'id': usr['pk']} for usr in User.objects.filter(username__contains=request.GET['q']).values('username', 'pk')]
    response_json = SafeString(simplejson.dumps(users_in_grp))
    return HttpResponse(response_json, mimetype='application/json')


@login_required(login_url='/login/')
def deleteGroup(request, gid):
    # if administrator is True
    try:
        if Membership.objects.get(group__id=gid, user=request.user).administrator:
            try:
                group = Group.objects.get(id=gid)
            except Group.DoesNotExist:
                # log error 404
                raise Http404
            group.deleted = True
            group.save()
        else:
            pass
    except:
        raise Http404
    return redirect('/home/')


@login_required(login_url='/login/')
def sentInvites(request, gid):
    '''
    '''
    if request.method == 'POST':
        groupRow = Group.objects.get(id=gid)
        users_invited = [User.objects.get(pk=id) for id in request.POST['members'].split(',')]
        groupRow.invite(request.user, users_invited)
    else:
        pass
    return redirect('/group/{0}/'.format(gid))


@login_required(login_url='/login/')
def changeGroup(request, gid):
    '''
    check if gid is valid
    default to personal
    '''
    request.session['active_group'] = Group.objects.get(pk=gid)
    if 'next' in request.GET:
        return redirect(request.GET['next'])
    else:
        return redirect('/home/')
