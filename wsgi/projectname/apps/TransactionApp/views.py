import json
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from TransactionApp.models import TransactionForm, Category, CategoryForm, UserCategory, GroupCategory
from django.utils.safestring import SafeString
from django.http import Http404, HttpResponse
from django.db.models import Q


@login_required(login_url='/login/')
def makeTransaction(request):
    categoryForm = CategoryForm()
    users_in_grp = [{'username': usr.username, 'id': usr.id, 'checked': False} for usr in User.objects.all()]
    fromCategory_user = [{'name': i.name, 'id': i.id} for i in request.user.usesCategories.filter(Q(category_type=0) | Q(category_type=2))]
    toCategory_user = [{'name': i.name, 'id': i.id} for i in request.user.usesCategories.filter(Q(category_type=1) | Q(category_type=2))]
    toCategory_group = [{'name': i.name, 'id': i.id} for i in request.user.usesCategories.filter(category_type=1)]
    response_json = dict()
    response_json['users_in_grp'] = SafeString(json.dumps(users_in_grp))
    response_json['fromCategory_user'] = SafeString(json.dumps(fromCategory_user))
    response_json['toCategory_user'] = SafeString(json.dumps(toCategory_user))
    response_json['toCategory_group'] = SafeString(json.dumps(toCategory_group))
    return render_to_response('makeTransaction.html', locals(), context_instance=RequestContext(request))


@login_required(login_url='/login/')
def createCategory(request, gid):
    '''
    always creates a category
    gid decised weather user-category or group-category needs to be created
    gid creates a group-category relation if not 0
    '''
    if request.method == 'GET':
        form = CategoryForm(request.GET)
        if form.is_valid():
            categoryRow = form.save(commit=False)
            categoryRow.created_by = request.user
            categoryRow.save()
            if gid == '0':
                UserCategory.objects.create(
                                        user=request.user,
                                        category=categoryRow,
                                        initial_amount=0,
                                        current_amount=0,
                                        deleted=False)
            else:
                GroupCategory.objects.create(
                                        group__id=gid,
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
            pass
            # form not valid exception
    else:
        pass
    return HttpResponse("done")


@login_required(login_url='/login/')
def getJSONcategories(request):
    fromCategory_user = [{'name': i.name, 'id': i.id} for i in Category.objects.all()]
    response_json = SafeString(json.dumps(fromCategory_user))
    return HttpResponse(response_json, mimetype='application/json')
