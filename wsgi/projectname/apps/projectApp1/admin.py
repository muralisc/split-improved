from django.contrib import admin
from projectApp1.models import Group, Membership, Category, Transaction, Payee

admin.site.register(Group)
admin.site.register(Membership)
admin.site.register(Category)
admin.site.register(Transaction)
admin.site.register(Payee)
