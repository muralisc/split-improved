from django.contrib import admin
from projectApp1.models import *
from TransactionApp.models import *


class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'create_time', 'privacy', 'deleted',)
    pass


class MembershipAdmin(admin.ModelAdmin):
    list_display = ('group', 'user', 'administrator', 'amount_in_pool', 'positions', 'deleted',)
    pass


class InviteAdmin(admin.ModelAdmin):
    list_display = ('from_user', 'to_user', 'group', 'unread', 'create_time', 'message', 'deleted',)
    pass


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category_type', 'description', 'created_by', 'create_time', 'privacy', 'deleted',)
    pass


class GroupCategoryAdmin(admin.ModelAdmin):
    list_display = ('group', 'category', 'initial_amount', 'current_amount', 'deleted',)
    pass


class UserCategoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'category', 'initial_amount', 'current_amount', 'deleted',)
    pass


class TransactionAdmin(admin.ModelAdmin):
    list_display = ('paid_user', 'amount', 'from_category', 'description', 'to_category',
                    'transaction_time', 'create_time', 'created_by_user', 'created_for_group',
                    'history', 'deleted')
    pass


class PayeeAdmin(admin.ModelAdmin):
    list_display = ('txn', 'user', 'outstanding_amount', 'deleted',)
    pass


#class Admin(admin.ModelAdmin):
#    list_display = ('', '', '', '', '',)
#    pass

admin.site.register(Group, GroupAdmin)
admin.site.register(Membership, MembershipAdmin)
admin.site.register(Invite, InviteAdmin)
admin.site.register(Notifiacation)

admin.site.register(Category, CategoryAdmin)
admin.site.register(GroupCategory, GroupCategoryAdmin)
admin.site.register(UserCategory, UserCategoryAdmin)
admin.site.register(Transaction, TransactionAdmin)
admin.site.register(Payee, PayeeAdmin)
