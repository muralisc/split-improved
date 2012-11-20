import json
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from TransactionApp.models import TransactionForm, Category
from django.utils.safestring import SafeString


@login_required(login_url='/login/')
def makeTransaction(request):
    form = TransactionForm()
    users_in_grp = [{'username': usr.username, 'id': usr.id, 'checked': False} for usr in User.objects.all()]
    category_user = [{'name': i.name, 'id': i.id} for i in Category.objects.all()]
    response_json = dict()
    response_json['users_in_grp'] = SafeString(json.dumps(users_in_grp))
    response_json['category_user'] = SafeString(json.dumps(category_user))
    return render_to_response('makeTransaction.html', locals(), context_instance=RequestContext(request))
