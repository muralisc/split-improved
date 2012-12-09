try:
    import simplejson as json
except ImportError:
    import json
import math
from datetime import datetime
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
#from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from TransactionApp.models import TransactionForm, Category, CategoryForm, UserCategory, GroupCategory, Transaction  # , Payee
from TransactionApp.helper import import_from_snapshot, get_outstanding_amount, get_expense, parseGET_initialise
from projectApp1.models import Membership  # , Group
from django.utils.safestring import SafeString
from django.http import Http404, HttpResponse
from django.db.models import Q  # , Sum


@login_required(login_url='/login/')
def displayTransactionForm(request):
    '''
    ensure that the session 'grp' is popuklated
    '''
    INCOME = Category.INCOME
    BANK = Category.BANK
    EXPENSE = Category.EXPENSE
    CREDIT = Category.CREDIT
    categoryForm = CategoryForm()
    response_json = dict()
    if request.user.has_perm('TransactionApp.group_transactions'):
        if 'active_group' in request.session:
            users_in_grp = [{
                            'username': mem_ship.user.username,
                            'id': mem_ship.user.id,
                            'checked': False
                            }
                            for mem_ship in request.session['active_group'].getMemberships.all()]
            toCategory_group = [{'name': i.name, 'id': i.id} for i in request.session['active_group'].usesCategories.filter(category_type=Category.EXPENSE)]
        else:
            users_in_grp = []
            toCategory_group = []
        response_json['users_in_grp'] = SafeString(json.dumps(users_in_grp))
        response_json['toCategory_group'] = SafeString(json.dumps(toCategory_group))
    if request.user.has_perm('TransactionApp.personal_transactions'):
        pass
    fromCategory_user = [{'name': i.name, 'id': i.id} for i in request.user.usesCategories.filter(
                                                                                    Q(category_type=Category.INCOME) |
                                                                                    Q(category_type=Category.BANK) |
                                                                                    Q(category_type=Category.CREDIT))]
    toCategory_user = [{'name': i.name, 'id': i.id} for i in request.user.usesCategories.filter(
                                                                                    Q(category_type=Category.EXPENSE) |
                                                                                    Q(category_type=Category.BANK) |
                                                                                    Q(category_type=Category.CREDIT))]
    response_json['fromCategory_user'] = SafeString(json.dumps(fromCategory_user))
    response_json['toCategory_user'] = SafeString(json.dumps(toCategory_user))
    return render_to_response('makeTransaction.html', locals(), context_instance=RequestContext(request))


@login_required(login_url='/login/')
def makeTransaction(request):
    '''
    create a transaction row in table if
    payee table row for group
    create a notifications
    update related fields
    return back to the original site
    '''
    form = TransactionForm(request.POST)
    if form.is_valid():
        transactionRow = form.save(commit=False)
        if transactionRow.transaction_time is None:
            transactionRow.transaction_time = datetime.datetime.now()
        # if the paid user is not the logged in user then ensure that the
        # from_category is None
        if transactionRow.paid_user_id != request.user.id and transactionRow.from_category is not None:
            transactionRow.from_category = None
        transactionRow.created_by_user_id = request.user.id
        transactionRow.created_for_group = request.session['active_group']
        transactionRow.deleted = False
        # ensure fron category belogs to pid user
        transactionRow.save()
        if 'group_checkbox' in request.POST:
            if form.cleaned_data['users_involved'] is not None:
                transactionRow.associatePayees(form.cleaned_data['users_involved'])
    else:
        raise Http404
    return redirect('/transactionForm/')


@login_required(login_url='/login/')
def createCategory(request, gid):
    '''
    always creates a category
    gid decised weather user-category or group-category needs to be created
    gid creates a group-category relation if not 0
    '''
    ############# prevent multiple usercategory objects
    if request.method == 'GET':
        form = CategoryForm(request.GET)
        if form.is_valid():
            if not Category.objects.filter(name__iexact=form.cleaned_data['name']).exists():
                categoryRow = form.save(commit=False)
                categoryRow.created_by = request.user
                categoryRow.save()
            else:
                categoryRow = Category.objects.get(name__iexact=form.cleaned_data['name'])
            if gid == '0':
                UserCategory.objects.create(
                                        user=request.user,
                                        category=categoryRow,
                                        initial_amount=0,
                                        current_amount=0,
                                        deleted=False)
            else:
                GroupCategory.objects.create(
                                        group_id=gid,
                                        category=categoryRow,
                                        initial_amount=0,
                                        current_amount=0,
                                        deleted=False)
            return HttpResponse(SafeString(json.dumps({
                                                    'name': categoryRow.name,
                                                    'id': categoryRow.id,
                                                    'category_type': categoryRow.category_type})),
                                mimetype='application/json')
        else:
            raise Http404
            # form not valid exception
    else:
        pass
    return HttpResponse("done")


@login_required(login_url='/login/')
def getJSONcategories(request):
    fromCategory_user = [{'name': i.name, 'id': i.id} for i in Category.objects.all()]
    response_json = SafeString(json.dumps(fromCategory_user))
    return HttpResponse(response_json, mimetype='application/json')


#@login_required(login_url='/login/')
def statistics(request):
    import_from_snapshot()
   #transaction_list_with_payee_list = [[temp, Payee.objects.filter(txn=temp)] for temp in transaction_list]
    return render_to_response('statistics.html', locals(), context_instance=RequestContext(request))


@login_required(login_url='/login/')
def groupStatistics(request):
    '''
    displays outstnding amount and expense
    '''
    (start_time, end_time) = parseGET_initialise(request)
    members = Membership.objects.filter(group=request.session['active_group'])
    members1 = list()
    for temp in members:
        members1.append([temp, get_expense(temp.group.id, temp.user.id, start_time, end_time)])
    return render_to_response('groupStatistics.html', locals(), context_instance=RequestContext(request))


@login_required(login_url='/login/')
def groupExpenseList(request):
    (start_time, end_time) = parseGET_initialise(request)
    if 'u' in request.GET:
        filter_user_id = int(request.GET['u'])
    else:
        filter_user_id = request.user.pk
    transaction_list = Transaction.objects.filter(
                        Q(created_for_group=request.session['active_group']) &                          # filter the group
                        Q(deleted=False) &                                                              # filter deleted
                        Q(transaction_time__range=(start_time, end_time)) &
                        (Q(paid_user_id=filter_user_id) | Q(users_involved__id__in=[filter_user_id]))   # for including all transaction to which user is conencted
                        ).distinct().order_by('transaction_time')
    transaction_list_with_expense = list()
    cumulative_exp = 0
    for temp in transaction_list:
        usrexp = temp.get_expense(filter_user_id)
        cumulative_exp = cumulative_exp + usrexp
        transaction_list_with_expense.append([temp, usrexp, cumulative_exp])
    transaction_list_with_expense.reverse()
    return render_to_response('groupExpenseList.html', locals(), context_instance=RequestContext(request))


@login_required(login_url='/login/')
def groupOutstandingList(request):
    '''
    Displays the entire list no Pagination for debugging
    '''
    if 'u' in request.GET:
        filter_user_id = int(request.GET['u'])
    else:
        filter_user_id = request.user.pk
    transaction_list = Transaction.objects.filter(
                        Q(created_for_group=request.session['active_group']) &                          # filter the group
                        Q(deleted=False) &                                                              # filter deleted
                        (Q(paid_user_id=filter_user_id) | Q(users_involved__id__in=[filter_user_id]))   # for including all transaction to which user is conencted
                        ).distinct().order_by('transaction_time')
    transaction_list_with_outstanding = list()
    cumulative_sum = 0
    for temp in transaction_list:
        usrcost = temp.get_outstanding_amount(filter_user_id)
        cumulative_sum = cumulative_sum + usrcost
        transaction_list_with_outstanding.append([temp, usrcost, cumulative_sum])
    transaction_list_with_outstanding.reverse()
    return render_to_response('groupOutstandingList.html', locals(), context_instance=RequestContext(request))


@login_required(login_url='/login/')
def groupTransactionList(request):
    '''
    Display 10 trnsactions perpage
    '''
    # XXX check for invalid 'page no' in GETS
    if 'u' in request.GET:
        filter_user_id = int(request.GET['u'])
    else:
        filter_user_id = request.user.pk
    if 'page' in request.GET:
        page_no = int(request.GET['page'])
    else:
        page_no = 1
    if 'rpp' in request.GET:
        txn_per_page = int(request.GET['rpp'])
    else:
        txn_per_page = 5
    transaction_list = Transaction.objects.filter(
                        Q(created_for_group_id=request.session['active_group'].id) &                    # filter the group
                        Q(deleted=False) &                                                              # filter deleted
                        (Q(paid_user_id=filter_user_id) | Q(users_involved__id__in=[filter_user_id]))   # for including all transaction to which user is conencted
                        ).distinct().order_by('-transaction_time')
    no_of_pages = math.ceil(float(transaction_list.count()) / txn_per_page)
    start_index = (page_no - 1) * txn_per_page
    end_index = page_no * txn_per_page
    transaction_list = transaction_list[start_index:end_index]
    transaction_list_with_outstanding = list()
    # cumulative_sum = Membership.objects.get(group=request.session['active_group'], user_id=filter_user_id).amount_in_pool
    cumulative_sum = get_outstanding_amount(request.session['active_group'], filter_user_id, transaction_list[0].transaction_time)
    for temp in transaction_list:
        usrcost = temp.get_outstanding_amount(filter_user_id)
        transaction_list_with_outstanding.append([temp, usrcost, cumulative_sum])
        cumulative_sum = cumulative_sum - usrcost
    return render_to_response('groupTransactionList.html', locals(), context_instance=RequestContext(request))
