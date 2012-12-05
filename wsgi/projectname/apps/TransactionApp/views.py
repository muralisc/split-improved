try:
    import simplejson as json
except ImportError:
    import json
import datetime
from django.utils.timezone import utc
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from TransactionApp.models import TransactionForm, Category, CategoryForm, UserCategory, GroupCategory, Payee, Transaction
from projectApp1.models import Membership
from django.utils.safestring import SafeString
from django.http import Http404, HttpResponse
from django.db.models import Q


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
            transactionRow.transaction_time = datetime.datetime.utcnow().replace(tzinfo=utc)
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


@login_required(login_url='/login/')
def statistics(request):
    #filter_user = request.user
    #filter_group = <> | None
    #Q(users_involved__in=filter_user)|Q(paid_user_id=filter_user.id)       #all transactoin involving filter_user
    #Q(created_for_group=filter_group)                                          #all transactoin involving filter_group
    transaction_filters = Q(deleted=False)
    transaction_list = Transaction.objects.filter(transaction_filters)
    transaction_list_with_payee_list = [[temp, Payee.objects.filter(txn=temp)] for temp in transaction_list]
    return render_to_response('statistics.html', locals(), context_instance=RequestContext(request))
