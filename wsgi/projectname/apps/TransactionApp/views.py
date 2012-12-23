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
from TransactionApp.helper import import_from_snapshot, get_outstanding_amount, get_expense, parseGET_initialise, get_page_info, new_group_transaction_event, new_personal_transaction_event
from TransactionApp.__init__ import INCOME, BANK, EXPENSE, CREDIT, THIS_MONTH, LAST_MONTH, CUSTOM_RANGE
from projectApp1.models import Membership  # , Group
from django.utils.safestring import SafeString
from django.http import Http404, HttpResponse
from django.db.models import Q, Sum


@login_required(login_url='/login/')
def displayTransactionForm(request):
    '''
    ensure that the session 'grp' is popuklated
    '''
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
            'INCOME': INCOME,
            'BANK':  BANK,
            'EXPENSE': EXPENSE,
            'CREDIT': CREDIT,
            }
    return render_to_response('makeTransaction.html', dict_for_html, context_instance=RequestContext(request))


@login_required(login_url='/login/')
def makeTransaction(request):
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
                transactionRow.save()
                if form.cleaned_data['users_involved'] is not None:
                    transactionRow.associatePayees(form.cleaned_data['users_involved'])
                new_group_transaction_event(request.session['active_group'].id, transactionRow, request.user.id)
                # NOw make the corrsponding personal entry
                newtransactionRow = deepcopy(transactionRow)
                newtransactionRow.id = None
                newtransactionRow.created_for_group = None
                newtransactionRow.description = 'sent to group' + request.session['active_group'].name
                newtransactionRow.to_category_id = None
                newtransactionRow.save()
                new_personal_transaction_event(request.user.id, newtransactionRow)
            else:
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
def editTransactionForm(request):
    '''
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
            transaction_to_edit = Transaction.objects.get(id=transaction_id) # TODO include group check too
            for mem_ship in request.session['active_group'].getMemberships.all():
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
            'INCOME': INCOME,
            'BANK':  BANK,
            'EXPENSE': EXPENSE,
            'CREDIT': CREDIT,
            }
    return render_to_response('makeTransaction.html', dict_for_html, context_instance=RequestContext(request))


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
    import_from_snapshot()
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
    (start_time, end_time, timeRange, filter_user_id, page_no, txn_per_page) = parseGET_initialise(request)
    members = Membership.objects.filter(group=request.session['active_group'])
    members1 = list()
    for temp in members:
        members1.append([temp, get_expense(temp.group.id, temp.user.id, start_time, end_time)])
    dict_for_html = {
            'members1': members1,
            'start_time': start_time,
            'end_time': end_time,
            'timeRange': timeRange,
            'request': request,
            'THIS_MONTH': THIS_MONTH,
            'LAST_MONTH': LAST_MONTH,
            'CUSTOM_RANGE': CUSTOM_RANGE,
            }
    return render_to_response('groupStatistics.html', dict_for_html, context_instance=RequestContext(request))


@login_required(login_url='/login/')
def groupExpenseList(request):
    (start_time, end_time, timeRange, filter_user_id, page_no, txn_per_page) = parseGET_initialise(request)
    transaction_list = Transaction.objects.filter(
                        Q(created_for_group_id=request.session['active_group'].id) &
                        Q(deleted=False) &
                        Q(transaction_time__range=(start_time, end_time)) &
                        (
                            Q(paid_user_id=filter_user_id) |        # for including all transaction to which user is conencted
                            Q(users_involved__id__in=[filter_user_id])
                        )
                        ).distinct().order_by('-transaction_time')
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
            'page_no': page_no,
            'txn_per_page': txn_per_page,
            'start_time': start_time,
            'current_page': current_page,
            'end_time': end_time,
            'timeRange': timeRange,
            'transaction_list_with_expense': transaction_list_with_expense,
            'paginator_obj': paginator_obj,
            'THIS_MONTH': THIS_MONTH,
            'LAST_MONTH': LAST_MONTH,
            'CUSTOM_RANGE': CUSTOM_RANGE
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
                        Q(created_for_group=request.session['active_group']) &
                        Q(deleted=False)
                        ).distinct().order_by(*['amount',])
    # TODO more sorting
    transaction_list_for_sorting = list()
    cumulative_sum = 0
    for temp in transaction_list:
        usrcost = temp.get_outstanding_amount(filter_user_id)
        cumulative_sum = cumulative_sum + usrcost
        transaction_list_for_sorting.append([temp, usrcost, cumulative_sum])
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
    # XXX check for invalid 'page no' in GETS
    (start_time, end_time, timeRange, filter_user_id, page_no, txn_per_page) = parseGET_initialise(request)
    transaction_list = Transaction.objects.filter(
                        Q(created_for_group_id=request.session['active_group'].id) &
                        Q(deleted=False) &
                        Q(transaction_time__range=(start_time, end_time)) &
                        (
                            Q(paid_user_id=filter_user_id) |        # for including all transaction to which user is conencted
                            Q(users_involved__id__in=[filter_user_id])
                        )
                        ).distinct().order_by('-transaction_time')
    (paginator_obj, current_page) = get_page_info(transaction_list, txn_per_page, page_no)
    transaction_list = current_page.object_list

    # populating the template array
    transaction_list_with_outstanding = list()
    # XXX in get is empty use cache withi=out calculating TODO
    if len(transaction_list) != 0:
        cumulative_sum = get_outstanding_amount(request.session['active_group'].id, filter_user_id, transaction_list[0].transaction_time)
    else:
        # TODO
        pass
    for temp in transaction_list:
        usrcost = temp.get_outstanding_amount(filter_user_id)
        transaction_list_with_outstanding.append([temp, usrcost, cumulative_sum])
        cumulative_sum = cumulative_sum - usrcost
    dict_for_html = {
            'page_no': page_no,
            'txn_per_page': txn_per_page,
            'start_time': start_time,
            'current_page': current_page,
            'end_time': end_time,
            'timeRange': timeRange,
            'transaction_list_with_outstanding': transaction_list_with_outstanding,
            'paginator_obj': paginator_obj,
            'THIS_MONTH': THIS_MONTH,
            'LAST_MONTH': LAST_MONTH,
            'CUSTOM_RANGE': CUSTOM_RANGE
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
            fc = int(request.GET['atofc'])
            tc = fc
            transacton_filters = transacton_filters & (
                                    Q(from_category_id=fc) |
                                    Q(to_category_id=tc)
                                    )
        except:
            fc = None
            tc = None
            pass
    else:
        try:
            fc = int(request.GET['fc'])
            transacton_filters = transacton_filters & Q(from_category_id=fc)
        except:
            fc = None
            pass
        try:
            tc = int(request.GET['tc'])
            transacton_filters = transacton_filters & Q(to_category_id=tc)
        except:
            tc = None
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
    (paginator_obj, current_page) = get_page_info(transaction_list, txn_per_page, page_no)
    transaction_list = current_page.object_list
    response_json = dict()
    category = [{
                'name': row.category.name,
                'id': row.category.id,
                'type': row.category.category_type,
                }
                for row in UserCategory.objects.filter(user_id=request.user.id)]
    response_json['category'] = SafeString(json.dumps(category))

    dict_for_html = {
            'page_no': page_no,
            'txn_per_page': txn_per_page,
            'start_time': start_time,
            'current_page': current_page,
            'end_time': end_time,
            'timeRange': timeRange,
            'transaction_list': transaction_list,
            'paginator_obj': paginator_obj,
            'response_json': response_json,
            'fc': fc,
            'tc': tc,
            'THIS_MONTH': THIS_MONTH,
            'LAST_MONTH': LAST_MONTH,
            'CUSTOM_RANGE': CUSTOM_RANGE,
            'INCOME': INCOME,
            'BANK':  BANK,
            'EXPENSE': EXPENSE,
            'CREDIT': CREDIT,
            }
    return render_to_response('personalTransactionList.html', dict_for_html, context_instance=RequestContext(request))

# TODO report errroers fu nction
# TODO user filer in all html pages
# TODO creating category of the same name
# TODO creating duplicate user cateories
# TODO transaction history
# view and move uncategorised transactions TODO
