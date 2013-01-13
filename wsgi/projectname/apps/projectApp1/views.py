from django.db import IntegrityError
try: import simplejson as json
except ImportError: import json
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.contrib.auth.models import User, Permission
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from projectApp1.forms import LoginCreateForm
from projectApp1.models import GroupForm, Membership, Group, Invite, Notification
from django.http import Http404, HttpResponse
from django.utils.safestring import SafeString
from TransactionApp.__init__ import INCOME, BANK, EXPENSE, CREDIT, THIS_MONTH, LAST_MONTH, CUSTOM_RANGE, ALL_TIME
from TransactionApp.helper import on_create_user, updateSession, get_outstanding_amount, get_expense, get_paid_amount, \
        parseGET_initialise, updateNotificationInvites


def createUser(request):
    if request.method == 'POST':
        form = LoginCreateForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            username = email
            password = form.cleaned_data['password']
            try:
                user = User.objects.create_user(username, email, password)
                user.save()
                on_create_user(user)
                newUserCreated = True
            except IntegrityError, e:
                userNameExist = "user name already exist"
        else:
            pass
            # form is invalid erros auto set TODO
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
                    updateSession(request)
                    if 'next_url' in request.session:
                        return redirect(request.session['next_url'])
                    else:
                        return redirect('/home/')
                else:
                    pass
                    # redirect ot 'dissabled account' TODO
            else:
                wrongUsernameOrPassword = True
        else:
            pass
            # form is invalid erros auto set TODO
    elif 'next' in request.GET:
        request.session['next_url'] = request.GET['next']
    form = LoginCreateForm()
    return render_to_response('loginCreate.html', locals(), context_instance=RequestContext(request))


@login_required(login_url='/login/')
def home(request):
    (start_time, end_time, timeRange, filter_user_id, page_no, txn_per_page) = parseGET_initialise(request)
    # TODO funtion to update no fo invires is session
    updateNotificationInvites(request)
    group_list = list()
    for temp in request.session['memberships']:
        group_list.append(
                [
                    temp.group,
                    get_outstanding_amount(temp.group.id, temp.user.id, start_time, end_time),
                    get_expense(temp.group.id, temp.user.id, start_time, end_time),
                    get_paid_amount(temp.group.id, temp.user.id, start_time, end_time)
                ]
                )
    dict_for_html = {
            'group_list': group_list,
            'request': request,
            'response_json': request.session['response_json'],
            'start_time': start_time,
            'end_time': end_time,
            'timeRange': timeRange,
            'THIS_MONTH': THIS_MONTH,
            'LAST_MONTH': LAST_MONTH,
            'CUSTOM_RANGE': CUSTOM_RANGE,
            'ALL_TIME': ALL_TIME,
            }
    return render_to_response('home.html', dict_for_html, context_instance=RequestContext(request))


@login_required(login_url='/login/')
def createGroupForm(request):
    form = GroupForm()
    dict_for_html = {
            'form': form,
            'request': request,
            'response_json': request.session['response_json'],
            }
    return render_to_response('createGroupForm.html', dict_for_html, context_instance=RequestContext(request))


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
    creates a group with one member; the creator is made admin
    '''
    if request.method == 'POST':
        form = GroupForm(request.POST)
        if form.is_valid():
            if not Group.objects.filter(name__iexact=form.cleaned_data['name']).exists():
                groupRow = form.save(commit=False)
                groupRow.privacy = 0
                groupRow.deleted = False
                groupRow.save()
                Membership.objects.create(
                                        group=groupRow,
                                        user=request.user,
                                        administrator=True,
                                        positions='creator',
                                        amount_in_pool=0
                                        )
                updateSession(request)
                try:
                    users_invited = [User.objects.get(pk=id) for id in request.POST['members'].split(',')]
                    groupRow.invite(request.user, users_invited)
                except:
                    pass
            else:
                #group alredy exists
                # TODO test for creating a groupname that alredy exists
                pass
        else:
            '''
            form error code
            '''
            raise Http404
    else:
        pass
    return redirect('/group/{0}/'.format(groupRow.id))


@login_required(login_url='/login/')
def groupHome(request, gid):
    try:
        group = Group.objects.get(id=gid, deleted=False)
    except Group.DoesNotExist:
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
                updateSession(request)
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
def showNotifications(request):
    new_notifications = [i for i in Notification.objects.filter(to_user=request.user, is_unread=True)]
    all_notifications = [i for i in Notification.objects.filter(to_user=request.user, is_unread=False)]
    Notification.objects.filter(to_user=request.user, is_unread=True).update(is_unread=False)
    updateNotificationInvites(request)
    return render_to_response('allNotifications.html', locals(), context_instance=RequestContext(request))


@login_required(login_url='/login/')
def getJSONusers(request):
    '''
    return all users whose name matches the query string as json
    '''
    users_in_grp = [
            {
                'name': usr['username'],
                'id': usr['pk']
            }
            for usr in User.objects.filter(username__contains=request.GET['q']).values('username', 'pk')]
    response_json = SafeString(json.dumps(users_in_grp))
    return HttpResponse(response_json, mimetype='application/json')


@login_required(login_url='/login/')
def deleteGroup(request, gid):
    # if administrator is True
    try:
        if Membership.objects.get(group__id=gid, user=request.user).administrator:
            try:
                group = Group.objects.get(id=gid)
            except Group.DoesNotExist:
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
    if request.method == 'POST':
        groupRow = Group.objects.get(id=gid)
        if Membership.objects.filter(group=groupRow).filter(user=request.user).exists():
            users_invited = [User.objects.get(pk=id) for id in request.POST['members'].split(',')]
            groupRow.invite(request.user, users_invited)
        else:
            raise Http404
    else:
        pass
    return redirect('/group/{0}/'.format(gid))


@login_required(login_url='/login/')
def changeGroup(request, gid):
    '''
    '''
    if Group.objects.filter(id=gid).exists():
        groupRow = Group.objects.get(id=gid)
    else:
        raise Http404
    if Membership.objects.filter(group=groupRow).filter(user=request.user).exists():
        request.session['active_group'] = groupRow
    else:
        raise Http404
    if 'next' in request.GET:
        return redirect(request.GET['next'])
    else:
        return redirect('/home/')


