try:
    import simplejson as json
except ImportError:
    import json
from copy import deepcopy
from datetime import datetime
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
#from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from TransactionApp.models import TransactionForm, Category, CategoryForm, UserCategory, GroupCategory, Transaction, Payee
from TransactionApp.helper import import_from_snapshot, get_outstanding_amount, get_expense, get_paid_amount, \
        parseGET_initialise, parseGET_ordering, get_page_info, new_group_transaction_event, new_personal_transaction_event, \
        delete_group_transaction_event
from TransactionApp.__init__ import INCOME, BANK, EXPENSE, CREDIT, THIS_MONTH, LAST_MONTH, CUSTOM_RANGE, ALL_TIME
from projectApp1.models import Membership  # , Group
from itertools import groupby
from django.utils.safestring import SafeString
from django.http import Http404, HttpResponse
from django.db.models import Q, Sum


@login_required(login_url='/login/')
def displayTransactionForm(request):
    '''
    ensure that the session 'grp' is popuklated
    '''
    categoryForm = CategoryForm()
    dict_for_html = {
            'categoryForm': CategoryForm,
            'response_json': request.session['response_json'],
            'request': request,
            'next_link': "/makeTransaction/",
            'INCOME': INCOME,
            'BANK':  BANK,
            'EXPENSE': EXPENSE,
            'CREDIT': CREDIT,
            }
    return render_to_response('makeTransaction.html', dict_for_html, context_instance=RequestContext(request))


@login_required(login_url='/login/')
def makeTransaction(request, called_for_edit=None):
    '''
    create a transaction row in table if
    payee table rows for transaction
    create a notifications
    return back to the original site
    base cases
    case1: user making txn with payee as user
    case2: user making txn with payee not contatinig user
    case3: somebody maing txn with user as a payee
    Error checks
    the user can check users involved and then dissable the group checkbox
    Update membership for group transactions amount inpool for each group txn
    Update user category model after a personal transaction
    '''
    # TODO send conflicting data
    # TODO 1 check box dissabled but usersInvolved non empty
    # TODO checkbox dissabled but non logged in user as user paid
    # TODO checkbox enabled but non logged in user as user paid and fromCategory of logged in user
    # TODO invalid to category value
    # TODO checkbox enabled with empty users involved list
    # TODO updater member ship outstsnding
    # TODO update usercategory outstsnding
    # TODO hoem page will get values form there field TODO
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
            transactionRow.deleted = False
            # making actual database entries
            # condition to check the type of txn user is trying to make
            if(
                    'group_checkbox' in request.POST or
                    'TransactionApp.personal_transactions' not in request.user.get_all_permissions()
                    ):
                # user is trying to make a group txn
                # check if the from category belongs to the user
                if(request.user.usesCategories.filter(pk=transactionRow.from_category_id).exists()):
                    pass
                else:
                    transactionRow.from_category_id = None
                # check if the to category belongs to the group
                if (request.session['active_group'].usesCategories.filter(pk=transactionRow.to_category_id).exists()):
                    pass
                else:
                    transactionRow.to_category_id = None
                # check if the user didnt pass any users_involved values
                if len(form.cleaned_data['users_involved']) == 0:
                    raise Http404
                transactionRow.created_for_group_id = request.session['active_group'].id
                try:
                    transactionRow.history_id = int(request.GET['t']) if 't' in request.GET else None
                except:
                    pass
                transactionRow.save()
                if form.cleaned_data['users_involved'] is not None:
                    transactionRow.associatePayees(form.cleaned_data['users_involved'])
                new_group_transaction_event(request.session['active_group'].id, transactionRow, request.user.id)
                if called_for_edit is not True:
                    transactionRow.create_notifications(request.user.id, 'txn_created')
                else:  # the transction is being editted
                    transactionRow.create_notifications(request.user.id, 'txn_edited')
                # NOw make the corrsponding personal entry
                # for every group transaction a personal transaction
                # entry is made for paid user
                newtransactionRow = deepcopy(transactionRow)
                newtransactionRow.id = None
                newtransactionRow.created_for_group = None
                newtransactionRow.description = 'sent to group' + request.session['active_group'].name
                newtransactionRow.to_category_id = None
                newtransactionRow.history_id = None
                newtransactionRow.save()
                new_personal_transaction_event(request.user.id, newtransactionRow)
            else:
                # the user is trying to make a personal transaction alone
                # check if the from category belongs to the user
                if(request.user.usesCategories.filter(pk=transactionRow.from_category_id).exists()):
                    pass
                else:
                    transactionRow.from_category_id = None
                # check if the to category belongs to the user
                if (request.user.usesCategories.filter(pk=transactionRow.to_category_id).exists()):
                    pass
                else:
                    transactionRow.to_category_id = None
                transactionRow.save()
                new_personal_transaction_event(request.user.id, transactionRow)
        else:
            raise Http404
    return redirect('/transactionForm/')


@login_required(login_url='/login/')
def deleteTransaction(request, called_for_edit=None):
    if 't' in request.GET:
        transaction_id = int(request.GET['t'])
    else:
        pass
    next_url = request.META['HTTP_REFERER']
    transactionRow = Transaction.objects.get(id=transaction_id)
    delete_group_transaction_event(request.session['active_group'].id, transactionRow, request.user.id)
    if called_for_edit is not True:
        transactionRow.create_notifications(request.user.id, 'txn_deleted')
    transactionRow.deleted = True
    transactionRow.save()
    return redirect(next_url)


@login_required(login_url='/login/')
def editTransactionForm(request):
    '''
    sents variables to initialize the angular js variables
    finds the position of paid_user in list and sends it as edit_paid_user
    '''
    if 't' in request.GET:
        transaction_id = int(request.GET['t'])
    else:
        return redirect('/transactionForm/')
    categoryForm = CategoryForm()
    response_json = dict()
    if request.user.has_perm('TransactionApp.group_transactions'):
        if 'active_group' in request.session:
            users_in_grp = []
            checked = False
            transaction_to_edit = Transaction.objects.get(id=transaction_id)  # TODO include group check too
            involving_checkbox_state = True if transaction_to_edit.created_for_group is not None else False
            paid_user_pos_found = False
            paid_user_pos = 0
            for mem_ship in request.session['active_group'].getMemberships.all():
                if mem_ship.user_id == transaction_to_edit.paid_user_id:
                    paid_user_pos_found = True
                elif paid_user_pos_found is False:
                    paid_user_pos = paid_user_pos + 1
                checked = True if Payee.objects.filter(txn_id=transaction_id, user_id=mem_ship.user.id).exists() else False
                users_in_grp.append({
                                'username': mem_ship.user.username,
                                'id': mem_ship.user.id,
                                'checked': checked
                                })
            toCategory_group = [{
                                    'name': i.name,
                                    'id': i.id
                                }
                                for i in request.session['active_group'].usesCategories.filter(category_type=EXPENSE)]
        else:
            users_in_grp = []
            toCategory_group = []
        response_json['users_in_grp'] = SafeString(json.dumps(users_in_grp))
        response_json['toCategory_group'] = SafeString(json.dumps(toCategory_group))
    if request.user.has_perm('TransactionApp.personal_transactions'):
        pass
    fromCategory_user = [{'name': i.name, 'id': i.id} for i in request.user.usesCategories.filter(
                                                                                    Q(category_type=INCOME) |
                                                                                    Q(category_type=BANK) |
                                                                                    Q(category_type=CREDIT))]
    toCategory_user = [{'name': i.name, 'id': i.id} for i in request.user.usesCategories.filter(
                                                                                    Q(category_type=EXPENSE) |
                                                                                    Q(category_type=BANK) |
                                                                                    Q(category_type=CREDIT))]
    response_json['fromCategory_user'] = SafeString(json.dumps(fromCategory_user))
    response_json['toCategory_user'] = SafeString(json.dumps(toCategory_user))

    dict_for_html = {
            'categoryForm': CategoryForm,
            'response_json': response_json,
            'request': request,
            'edit_date': transaction_to_edit.transaction_time.strftime('%Y-%m-%d'),
            'edit_id': transaction_to_edit.id,
            'edit_description': transaction_to_edit.description,
            'edit_amount': transaction_to_edit.amount,
            'edit_paid_user': paid_user_pos,
            'involving_checkbox_state': involving_checkbox_state,
            'next_link': "/editTransaction/",
            'INCOME': INCOME,
            'BANK':  BANK,
            'EXPENSE': EXPENSE,
            'CREDIT': CREDIT,
            }
    return render_to_response('makeTransaction.html', dict_for_html, context_instance=RequestContext(request))


@login_required(login_url='/login/')
def editTransaction(request):
    deleteTransaction(request, called_for_edit=True)
    makeTransaction(request, called_for_edit=True)
    return redirect('/transactionForm/')


@login_required(login_url='/login/')
def createCategory(request, gid):
    '''
    always creates a category
    checks weather a group already exist
    gid decised weather user-category or group-category needs to be created
    gid creates a group-category relation if not 0
    '''
    ############# prevent multiple usercategory objects TODO
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
                if not UserCategory.objects.filter(user=request.user, category=categoryRow).exists():
                    UserCategory.objects.create(
                                            user=request.user,
                                            category=categoryRow,
                                            initial_amount=0,
                                            current_amount=0,
                                            deleted=False)
            else:
                if not GroupCategory.objects.filter(group_id=gid, category=categoryRow).exists():
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
            # form not valid exception TODO
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
    if request.method == 'POST':
        import_from_snapshot(request)
    return render_to_response('import.html', locals(), context_instance=RequestContext(request))


'''
TransactionFn is for supporint reorder and sort
OutstandingFn is for viewing cumulstive outstnding at various filters
ExpenseFn is for cumulative expenses at various filters
'''


@login_required(login_url='/login/')
def groupStatistics(request):
    '''
    displays outstnding amount and expense
    '''
    (
            start_time,
            end_time,
            timeRange,
            filter_user_id,
            page_no,
            txn_per_page
                            ) = parseGET_initialise(request)
    members = Membership.objects.filter(group=request.session['active_group'])
    members1 = list()
    for temp in members:
        members1.append(
                [
                    temp,
                    get_outstanding_amount(temp.group.id, temp.user.id, start_time, end_time),
                    get_expense(temp.group.id, temp.user.id, start_time, end_time),
                    get_paid_amount(temp.group.id, temp.user.id, start_time, end_time)
                ]
                )
    dict_for_html = {
            'members1': members1,
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
    return render_to_response('groupStatistics.html', dict_for_html, context_instance=RequestContext(request))


@login_required(login_url='/login/')
def groupSettle(request):
    members = Membership.objects.filter(group=request.session['active_group'])
    dict_for_html = {
            'members': members,
            'request': request,
            'ALL_TIME': ALL_TIME,
            }
    return render_to_response('groupSettle.html', dict_for_html, context_instance=RequestContext(request))


@login_required(login_url='/login/')
def groupExpenseList(request):
    (
            start_time,
            end_time,
            timeRange,
            filter_user_id,
            page_no,
            txn_per_page
                            ) = parseGET_initialise(request)
    (order_by_args, order_by_page_list) = parseGET_ordering(request)
    transaction_list = Transaction.objects.filter(
                        Q(created_for_group_id=request.session['active_group'].id) &
                        Q(deleted=False) &
                        Q(transaction_time__range=(start_time, end_time)) &
                        (
                            Q(paid_user_id=filter_user_id) |        # for including all transaction to which user is conencted
                            Q(users_involved__id__in=[filter_user_id])
                        )
                        ).distinct().order_by(*order_by_args)
    (paginator_obj, current_page) = get_page_info(transaction_list, txn_per_page, page_no)
    transaction_list = current_page.object_list
    # populating the transaction_list_with_expense array
    transaction_list_with_expense = list()
    if len(transaction_list) != 0:
        cumulative_exp = get_expense(request.session['active_group'], filter_user_id, start_time, transaction_list[0].transaction_time)
    else:
        # TODO
        pass
    for temp in transaction_list:
        usrexp = temp.get_expense(filter_user_id)
        transaction_list_with_expense.append([temp, usrexp, cumulative_exp])
        cumulative_exp = cumulative_exp - usrexp
    dict_for_html = {
            'transaction_list_with_expense': transaction_list_with_expense,
            'request': request,
            'response_json': request.session['response_json'],
            'filter_user_id': filter_user_id,
            'start_time': start_time,
            'end_time': end_time,
            'timeRange': timeRange,
            'page_no': page_no,
            'current_page': current_page,
            'txn_per_page': txn_per_page,
            'paginator_obj': paginator_obj,
            'THIS_MONTH': THIS_MONTH,
            'LAST_MONTH': LAST_MONTH,
            'CUSTOM_RANGE': CUSTOM_RANGE,
            'ALL_TIME': ALL_TIME,
            }
    return render_to_response('groupExpenseList.html', dict_for_html, context_instance=RequestContext(request))


@login_required(login_url='/login/')
def groupTransactionList(request):
    '''
    Displays the entire list
    no Pagination
    mainly for debugging
    '''
    (
            start_time,
            end_time,
            timeRange,
            filter_user_id,
            page_no,
            txn_per_page
                            ) = parseGET_initialise(request)
    (order_by_args, order_by_page_list) = parseGET_ordering(request)
    transaction_list = Transaction.objects.filter(
                        Q(created_for_group=request.session['active_group']) &
                        Q(deleted=False) &
                        Q(transaction_time__range=(start_time, end_time))
                        ).distinct().order_by(*order_by_args)
    (paginator_obj, current_page) = get_page_info(transaction_list, txn_per_page, page_no)
    transaction_list = current_page.object_list
    # TODO more sorting
    transaction_list_for_sorting = list()
    cumulative_sum = 0
    for temp in transaction_list:
        transaction_list_for_sorting.append(temp)
    dict_for_html = {
            'transaction_list_for_sorting': transaction_list_for_sorting,
            'request': request,
            'response_json': request.session['response_json'],
            'filter_user_id': filter_user_id,
            'start_time': start_time,
            'end_time': end_time,
            'timeRange': timeRange,
            'page_no': page_no,
            'current_page': current_page,
            'txn_per_page': txn_per_page,
            'paginator_obj': paginator_obj,
            'THIS_MONTH': THIS_MONTH,
            'LAST_MONTH': LAST_MONTH,
            'CUSTOM_RANGE': CUSTOM_RANGE,
            'ALL_TIME': ALL_TIME,
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
    # XXX check for invalid 'page no' in GETS
    (
            start_time,
            end_time,
            timeRange,
            filter_user_id,
            page_no,
            txn_per_page
                            ) = parseGET_initialise(request)
    (order_by_args, order_by_page_list) = parseGET_ordering(request)
    transaction_list = Transaction.objects.filter(
                        Q(created_for_group_id=request.session['active_group'].id) &
                        Q(deleted=False) &
                        Q(transaction_time__range=(start_time, end_time)) &
                        (
                            Q(paid_user_id=filter_user_id) |        # for including all transaction to which user is conencted
                            Q(users_involved__id__in=[filter_user_id])
                        )
                        ).distinct().order_by(*order_by_args)
    (paginator_obj, current_page) = get_page_info(transaction_list, txn_per_page, page_no)
    transaction_list = current_page.object_list

    # populating the template array
    transaction_list_with_outstanding = list()
    # XXX in get is empty use cache withi=out calculating TODO
    if len(transaction_list) != 0:
        cumulative_sum = get_outstanding_amount(request.session['active_group'].id, filter_user_id, end_time=transaction_list[0].transaction_time)
    else:
        # TODO
        pass
    for temp in transaction_list:
        usrcost = temp.get_outstanding_amount(filter_user_id)
        transaction_list_with_outstanding.append([temp, usrcost, cumulative_sum])
        cumulative_sum = cumulative_sum - usrcost
    dict_for_html = {
            'transaction_list_with_outstanding': transaction_list_with_outstanding,
            'request': request,
            'response_json': request.session['response_json'],
            'filter_user_id': filter_user_id,
            'start_time': start_time,
            'end_time': end_time,
            'timeRange': timeRange,
            'page_no': page_no,
            'current_page': current_page,
            'txn_per_page': txn_per_page,
            'paginator_obj': paginator_obj,
            'THIS_MONTH': THIS_MONTH,
            'LAST_MONTH': LAST_MONTH,
            'CUSTOM_RANGE': CUSTOM_RANGE,
            'ALL_TIME': ALL_TIME,
            }
    return render_to_response('groupOutstandingList.html', dict_for_html, context_instance=RequestContext(request))


@login_required(login_url='/login/')
def groupPaidList(request):
    (
            start_time,
            end_time,
            timeRange,
            filter_user_id,
            page_no,
            txn_per_page
                            ) = parseGET_initialise(request)
    (order_by_args, order_by_page_list) = parseGET_ordering(request)
    transaction_list = Transaction.objects.filter(
                        Q(created_for_group_id=request.session['active_group'].id) &
                        Q(deleted=False) &
                        Q(transaction_time__range=(start_time, end_time)) &
                        (
                            Q(paid_user_id=filter_user_id)
                        )
                        ).distinct().order_by(*order_by_args)
    (paginator_obj, current_page) = get_page_info(transaction_list, txn_per_page, page_no)
    transaction_list = current_page.object_list

    transaction_list_with_paid = list()
    if len(transaction_list) != 0:
        cumulative_paid_amt = get_paid_amount(request.session['active_group'], filter_user_id, start_time, transaction_list[0].transaction_time)
    else:
        # TODO
        pass
    for temp in transaction_list:
        usr_paid = temp.amount
        transaction_list_with_paid.append([temp, usr_paid, cumulative_paid_amt])
        cumulative_paid_amt = cumulative_paid_amt - usr_paid
    dict_for_html = {
            'transaction_list_with_paid': transaction_list_with_paid,
            'request': request,
            'response_json': request.session['response_json'],
            'filter_user_id': filter_user_id,
            'start_time': start_time,
            'end_time': end_time,
            'timeRange': timeRange,
            'page_no': page_no,
            'current_page': current_page,
            'txn_per_page': txn_per_page,
            'paginator_obj': paginator_obj,
            'THIS_MONTH': THIS_MONTH,
            'LAST_MONTH': LAST_MONTH,
            'CUSTOM_RANGE': CUSTOM_RANGE,
            'ALL_TIME': ALL_TIME,
            }
    return render_to_response('groupPaidList.html', dict_for_html, context_instance=RequestContext(request))


@login_required(login_url='/login/')
def personalStatistics(request):
    (
            start_time,
            end_time,
            timeRange,
            filter_user_id,
            page_no,
            txn_per_page
                            ) = parseGET_initialise(request)
    user_categories = UserCategory.objects.filter(user_id=request.user.id).order_by('category__category_type')
    user_categories = sorted(user_categories, key=lambda x: x.category.category_type)
    expense_category_list = None
    income_category_list = None
    bank_category_list = None
    for keys, grp in groupby(user_categories, key=lambda x: x.category.category_type):
        if keys == EXPENSE:
            expense_category_list = list(grp)
        if keys == INCOME:
            income_category_list = list(grp)
        if keys == BANK:
            bank_category_list = list(grp)
    expense_category_outstanding_list = list()
    if expense_category_list is not None:
        for temp in expense_category_list:
            expense_category_outstanding_list.append([temp, temp.get_outstnading(start_time, end_time)])
    income_category_outstanding_list = list()
    if income_category_list is not None:
        for temp in income_category_list:
            income_category_outstanding_list.append([temp, temp.get_outstnading()])
    bank_category_outstanding_list = list()
    if bank_category_list is not None:
        for temp in bank_category_list:
            bank_category_outstanding_list.append([temp, temp.get_outstnading()])
    dict_for_html = {
            'request': request,
            'expense_category_outstanding_list': expense_category_outstanding_list,
            'income_category_outstanding_list': income_category_outstanding_list,
            'bank_category_outstanding_list': bank_category_outstanding_list,
            'response_json': request.session['response_json'],
            'start_time': start_time,
            'end_time': end_time,
            'timeRange': timeRange,
            'THIS_MONTH': THIS_MONTH,
            'LAST_MONTH': LAST_MONTH,
            'CUSTOM_RANGE': CUSTOM_RANGE,
            'ALL_TIME': ALL_TIME,
            }
    return render_to_response('personalStatistics.html', dict_for_html, context_instance=RequestContext(request))


@login_required(login_url='/login/')
def personalTransactionList(request):
    transacton_filters = Q()
    # all transactions of category
    if('atofc' in request.GET):
        try:
            atofc = int(request.GET['atofc'])
            fc = int(request.GET['atofc'])
            tc = fc
            transacton_filters = transacton_filters & (
                                    Q(from_category_id=fc) |
                                    Q(to_category_id=tc)
                                    )
        except:
            atofc = -1      # an invalid value
            fc = ""
            tc = ""
            pass
    else:
        atofc = -1      # an invalid value
        try:
            fc = int(request.GET['fc'])
            transacton_filters = transacton_filters & Q(from_category_id=fc)
        except:
            fc = ""
            pass
        try:
            tc = int(request.GET['tc'])
            transacton_filters = transacton_filters & Q(to_category_id=tc)
        except:
            tc = ""
            pass
    (
            start_time,
            end_time,
            timeRange,
            filter_user_id,
            page_no,
            txn_per_page
                            ) = parseGET_initialise(request)
    transaction_list = Transaction.objects.filter(
                        Q(created_for_group=None) &
                        Q(deleted=False) &
                        Q(transaction_time__range=(start_time, end_time)) &
                        Q(paid_user_id=filter_user_id) &
                        Q(users_involved__id=None)
                        ).filter(
                            transacton_filters
                        ).distinct().order_by('-transaction_time')
    (paginator_obj, current_page) = get_page_info(transaction_list, txn_per_page, page_no)
    transaction_list = current_page.object_list

    dict_for_html = {
            'display_category': True,
            'personal_transaction_list': transaction_list,
            'atofc': atofc,
            'fc': fc,
            'tc': tc,
            'response_json': request.session['response_json'],
            'start_time': start_time,
            'end_time': end_time,
            'timeRange': timeRange,
            'page_no': page_no,
            'current_page': current_page,
            'txn_per_page': txn_per_page,
            'paginator_obj': paginator_obj,
            'THIS_MONTH': THIS_MONTH,
            'LAST_MONTH': LAST_MONTH,
            'CUSTOM_RANGE': CUSTOM_RANGE,
            'ALL_TIME': ALL_TIME,
            'INCOME': INCOME,
            'BANK':  BANK,
            'EXPENSE': EXPENSE,
            'CREDIT': CREDIT,
            }
    return render_to_response('personalTransactionList.html', dict_for_html, context_instance=RequestContext(request))


@login_required(login_url='/login/')
def transactionHistory(request):
    if 't' in request.GET:
        transaction_id = int(request.GET['t'])
    else:
        # TODO redirect
        pass
    temp_txn = Transaction.objects.get(id=transaction_id)
    history_transaction_list = list()
    history_transaction_list.append(temp_txn)
    while temp_txn.history is not None:
        temp_txn = temp_txn.history
        history_transaction_list.append(temp_txn)
        pass
    dict_for_html = {
            'history_transaction_list': history_transaction_list,
            }
    return render_to_response('historyList.html', dict_for_html, context_instance=RequestContext(request))
# TODO report errroers fu nction
# TODO user filer in all html pages
# TODO creating category of the same name
# TODO creating duplicate user cateories
# TODO transaction history
# view and move uncategorised transactions TODO
# TODO check [test] delte txn reflect properly on totals personal and group
