from django.contrib import admin
from projectApp1.models import *
from TransactionApp.models import *

admin.site.register(Group)
admin.site.register(Membership)
admin.site.register(Category)
admin.site.register(Transaction)
admin.site.register(Payee)
admin.site.register(Invite)
admin.site.register(Notifiacation)
