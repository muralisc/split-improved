try:
    import simplejson as json
except ImportError:
    import json
import math
import itertools
from copy import deepcopy
from datetime import datetime
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
#from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from TransactionApp.models import TransactionForm, Category, CategoryForm, UserCategory, GroupCategory, Transaction  # , Payee
from TransactionApp.helper import import_from_snapshot, get_outstanding_amount, get_expense, parseGET_initialise
from projectApp1.models import Membership  # , Group
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils.safestring import SafeString
from django.http import Http404, HttpResponse
from django.db.models import Q, Sum


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
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            transactionRow = form.save(commit=False)
            if transactionRow.transaction_time is None:
                transactionRow.transaction_time = datetime.now()
            # if the paid user is not the logged in user then ensure that the from_category is None
            if transactionRow.paid_user_id != request.user.id and transactionRow.from_category is not None:
                transactionRow.from_category = None
            transactionRow.created_by_user_id = request.user.id
            transactionRow.created_for_group = request.session['active_group']
            transactionRow.deleted = False
            # if user has both permission, 'group_checkbox' should be checked for group txn
            if request.user.has_perms(['TransactionApp.group_transactions', 'TransactionApp.personal_transactions']) and 'group_checkbox' in request.POST:
                # if txn has from cateory and it belongs to request.user and paiduser = request.user then we need to duplicate the transaction
                if (transactionRow.from_category is not None and
                        UserCategory.objects.filter(user_id=request.user.id, category_id=transactionRow.from_category_id).exists() and
                        request.user.id == transactionRow.paid_user_id):
                    # 1 personal
                    temp_cfg = transactionRow.created_for_group
                    temp_tc = transactionRow.to_category
                    transactionRow.created_for_group = None
                    transactionRow.to_category = None
                    # ensure fron category belogs to pid user TODO
                    transactionRow.save()
                    # 2 group
                    newtransactionRow = deepcopy(transactionRow)
                    newtransactionRow.id = None
                    newtransactionRow.from_category = None
                    newtransactionRow.created_for_group = temp_cfg
                    newtransactionRow.to_category = temp_tc
                    newtransactionRow.save()
                else:
                    transactionRow.save()
                if form.cleaned_data['users_involved'] is not None:
                    transactionRow.associatePayees(form.cleaned_data['users_involved'])
            # if user had group permission alone meke group txn alone[checkbox wont be displayed]
            elif request.user.has_perm('TransactionApp.group_transactions'):
                transactionRow.save()
                if form.cleaned_data['users_involved'] is not None:
                    transactionRow.associatePayees(form.cleaned_data['users_involved'])
            # case user is making a personal transaction
            elif request.user.has_perm('TransactionApp.personal_transactions') and 'group_checkbox' not in request.POST:
                transactionRow.save()
                # TODO make sure tat both categories are enabled
                pass
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
def import_from_json(request):
    import_from_snapshot()
   #transaction_list_with_payee_list = [[temp, Payee.objects.filter(txn=temp)] for temp in transaction_list]
    return render_to_response('import.html', locals(), context_instance=RequestContext(request))


@login_required(login_url='/login/')
def groupStatistics(request):
    '''
    displays outstnding amount and expense
    '''
    (start_time, end_time, timeRange, filter_user_id, page_no, txn_per_page) = parseGET_initialise(request)
    members = Membership.objects.filter(group=request.session['active_group'])
    members1 = list()
    for temp in members:
        members1.append([temp, get_expense(temp.group.id, temp.user.id, start_time, end_time)])
    no_of_pages = 1   # for angularjs
    dict_for_html = {
            'members1': members1,
            'start_time': start_time,
            'end_time': end_time,
            'timeRange': timeRange,
            'request': request
            }
    return render_to_response('groupStatistics.html', dict_for_html, context_instance=RequestContext(request))


@login_required(login_url='/login/')
def groupExpenseList(request):
    (start_time, end_time, timeRange, filter_user_id, page_no, txn_per_page) = parseGET_initialise(request)
    transaction_list = Transaction.objects.filter(
                        Q(created_for_group=request.session['active_group']) &                          # filter the group
                        Q(deleted=False) &                                                              # filter deleted
                        Q(transaction_time__range=(start_time, end_time)) &
                        (Q(paid_user_id=filter_user_id) | Q(users_involved__id__in=[filter_user_id]))   # for including all transaction to which user is conencted
                        ).distinct().order_by('transaction_time')
    # Pagination stuff
    paginator_obj = Paginator(transaction_list, txn_per_page)
    try:
        current_page = paginator_obj.page(page_no)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        current_page = paginator_obj.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        current_page = paginator_obj.page(paginator_obj.num_pages)
    transaction_list = current_page.object_list
    no_of_pages = paginator_obj.num_pages

    # populating the template array
    transaction_list_with_expense = list()
    cumulative_exp = 0
    for temp in transaction_list:
        usrexp = temp.get_expense(filter_user_id)
        cumulative_exp = cumulative_exp + usrexp
        transaction_list_with_expense.append([temp, usrexp, cumulative_exp])
    transaction_list_with_expense.reverse()
    dict_for_html = {
            'page_no': page_no,
            'txn_per_page': txn_per_page,
            'no_of_pages': no_of_pages,
            'start_time': start_time,
            'current_page': current_page,
            'end_time': end_time,
            'timeRange': timeRange,
            'transaction_list_with_expense': transaction_list_with_expense,
            'paginator_obj': paginator_obj,
            #'THIS_MONTH': THIS_MONTH,
            #'LAST_MONTH': LAST_MONTH,
            #'CUSTOM_RANGE': CUSTOM_RANGE
            }
    return render_to_response('groupExpenseList.html', dict_for_html, context_instance=RequestContext(request))


@login_required(login_url='/login/')
def groupTransactionList(request):
    '''
    Displays the entire list
    no Pagination
    mainly for debugging
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
    transaction_list_for_sorting = list()
    cumulative_sum = 0
    for temp in transaction_list:
        usrcost = temp.get_outstanding_amount(filter_user_id)
        cumulative_sum = cumulative_sum + usrcost
        transaction_list_for_sorting.append([temp, usrcost, cumulative_sum])
    transaction_list_for_sorting.reverse()
    dict_for_html = {
            'transaction_list_for_sorting': transaction_list_for_sorting,
            }
    return render_to_response('groupTransactionList.html', dict_for_html, context_instance=RequestContext(request))


@login_required(login_url='/login/')
def groupOutstandingList(request):
    '''
    Display x trnsactions perpage based on time range
    '''
    # TODO test for the varivles sent for rendering are proper in value and type
    # verify the calculations in TODO all helper functions
    # TODO modifi
    # Trandsctoin is for supporint reorder and sort
    # Ourstndi is milyf or  cumulstive outstnding
    # Expense is for cumulstive exoense
    # XXX check for invalid 'page no' in GETS
    (start_time, end_time, timeRange, filter_user_id, page_no, txn_per_page) = parseGET_initialise(request)
    transaction_list = Transaction.objects.filter(
                        Q(created_for_group_id=request.session['active_group'].id) &                    # filter the group
                        Q(deleted=False) &                                                              # filter deleted
                        Q(transaction_time__range=(start_time, end_time)) &
                        (Q(paid_user_id=filter_user_id) | Q(users_involved__id__in=[filter_user_id]))   # for including all transaction to which user is conencted
                        ).distinct().order_by('-transaction_time')
    # Pagination stuff
    paginator_obj = Paginator(transaction_list, txn_per_page)
    try:
        current_page = paginator_obj.page(page_no)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        current_page = paginator_obj.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        current_page = paginator_obj.page(paginator_obj.num_pages)
    transaction_list = current_page.object_list
    no_of_pages = paginator_obj.num_pages

    # populating the template array
    transaction_list_with_outstanding = list()
    # XXX in get is empty use cache withi=out calculating
    # cumulative_sum = Membership.objects.get(group=request.session['active_group'], user_id=filter_user_id).amount_in_pool
    cumulative_sum = get_outstanding_amount(request.session['active_group'], filter_user_id, transaction_list[0].transaction_time)
    for temp in transaction_list:
        usrcost = temp.get_outstanding_amount(filter_user_id)
        transaction_list_with_outstanding.append([temp, usrcost, cumulative_sum])
        cumulative_sum = cumulative_sum - usrcost
    dict_for_html = {
            'page_no': page_no,
            'txn_per_page': txn_per_page,
            'no_of_pages': no_of_pages,
            'start_time': start_time,
            'current_page': current_page,
            'end_time': end_time,
            'timeRange': timeRange,
            'transaction_list_with_outstanding': transaction_list_with_outstanding,
            'paginator_obj': paginator_obj,
            #'THIS_MONTH': THIS_MONTH,
            #'LAST_MONTH': LAST_MONTH,
            #'CUSTOM_RANGE': CUSTOM_RANGE
            }
    return render_to_response('groupOutstandingList.html', dict_for_html, context_instance=RequestContext(request))


@login_required(login_url='/login/')
def personalStatistics(request):
    asd = UserCategory.objects.filter(user_id=request.user.id).order_by('category__category_type')
    category_outstanding_list = list()
    for temp in asd:
        category_lost = Transaction.objects.filter(
                                        from_category_id=temp.id,
                                    ).aggregate(
                                        Sum('amount')
                                    )['amount__sum']
        category_lost = category_lost if category_lost else 0
        category_gained = Transaction.objects.filter(
                                        to_category_id=temp.id,
                                    ).aggregate(
                                        Sum('amount')
                                    )['amount__sum']
        category_gained = category_gained if category_gained else 0
        category_outstanding_list.append([temp, category_gained - category_lost + temp.initial_amount])
    category_outstanding_list = sorted(category_outstanding_list, key=lambda x: x[0].category.category_type)
    dict_for_html = {
            'category_outstanding_list': category_outstanding_list,
            }
    return render_to_response('personalStatistics.html', dict_for_html, context_instance=RequestContext(request))


@login_required(login_url='/login/')
def personalTransactionList(request):
    transacton_filters = Q()
    # all transactions of category
    if('atofc' in request.GET):
        try:
            transacton_filters = transacton_filters & (
                                    Q(from_category_id=int(request.GET['atofc'])) |
                                    Q(to_category_id=int(request.GET['atofc']))
                                    )
        except:
            pass
    else:
        try:
            transacton_filters = transacton_filters & Q(from_category_id=int(request.GET['fc']))
        except:
            pass
        try:
            transacton_filters = transacton_filters & Q(to_category_id=int(request.GET['tc']))
        except:
            pass
    (start_time, end_time, timeRange, filter_user_id, page_no, txn_per_page) = parseGET_initialise(request)
    transaction_list = Transaction.objects.filter(
                        Q(created_for_group=None) &
                        Q(deleted=False) &
                        Q(transaction_time__range=(start_time, end_time)) &
                        Q(paid_user_id=filter_user_id) &
                        Q(users_involved__id=None)
                        ).filter(
                            transacton_filters
                        ).distinct().order_by('-transaction_time')
    # Pagination stuff
    paginator_obj = Paginator(transaction_list, txn_per_page)
    try:
        current_page = paginator_obj.page(page_no)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        current_page = paginator_obj.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        current_page = paginator_obj.page(paginator_obj.num_pages)
    transaction_list = current_page.object_list
    no_of_pages = paginator_obj.num_pages

    dict_for_html = {
            'page_no': page_no,
            'txn_per_page': txn_per_page,
            'no_of_pages': no_of_pages,
            'start_time': start_time,
            'current_page': current_page,
            'end_time': end_time,
            'timeRange': timeRange,
            'transaction_list': transaction_list,
            }
    return render_to_response('personalTransactionList.html', dict_for_html, context_instance=RequestContext(request))
