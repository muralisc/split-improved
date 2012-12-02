from django.contrib import admin
from projectApp1.models import *
from TransactionApp.models import *


class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'create_time', 'privacy', 'deleted',)
    pass


class MembershipAdmin(admin.ModelAdmin):
    list_display = ('group', 'user', 'administrator', 'amount_in_pool', 'positions',)
    pass


class InviteAdmin(admin.ModelAdmin):
    list_display = ('from_user', 'to_user', 'group', 'unread', 'create_time', 'message',)
    pass


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category_type', 'description', 'created_by', 'create_time', 'privacy',)
    pass

#class InviteAdmin(admin.ModelAdmin):
#    list_display = ('', '', '', '', '',)
#    pass

admin.site.register(Group, GroupAdmin)
admin.site.register(Membership, MembershipAdmin)
admin.site.register(Invite, InviteAdmin)
admin.site.register(Notifiacation)

admin.site.register(Category, CategoryAdmin)
admin.site.register(GroupCategory)
admin.site.register(UserCategory)
admin.site.register(Transaction)
admin.site.register(Payee)
