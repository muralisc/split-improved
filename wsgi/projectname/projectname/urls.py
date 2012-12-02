from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.views.generic.simple import redirect_to
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
    (r'^$', redirect_to, {'url': '/login/'}),
    (r'^login/$', 'projectApp1.views.siteLogin'),
    (r'^createUser/', 'projectApp1.views.createUser'),
    (r'^createGroup/', 'projectApp1.views.createGroup'),
    (r'^home/$', 'projectApp1.views.home'),
    (r'^settings/$', 'projectApp1.views.settings'),
    (r'^permission/(\w+)/(enable|dissable)/$', 'projectApp1.views.enableDissablePermissions'),
    (u'^transactionForm/$', 'TransactionApp.views.displayTransactionForm'),
    (r'^makeTransaction/$', 'TransactionApp.views.makeTransaction'),
    (r'^group/(\d+)/$', 'projectApp1.views.groupHome'),
    (r'^invite/(accept|decline)/(\d+)/$', 'projectApp1.views.changeInvite'),
    (r'^allInvites/$', 'projectApp1.views.showInvites'),
    (r'^getJSON/users/$', 'projectApp1.views.getJSONusers'),
    (r'^deleteGroup/(\d+)/$', 'projectApp1.views.deleteGroup'),
    (r'^sentInvites/(\d+)/$', 'projectApp1.views.sentInvites'),
    (r'^changeGroup/(\d+)/$', 'projectApp1.views.changeGroup'),


    (r'^createCategory/(\d+)/$', 'TransactionApp.views.createCategory'),
    (r'^getJSONcategories/$', 'TransactionApp.views.getJSONcategories'),

    (r'^logout/$', 'django.contrib.auth.views.logout_then_login', {'login_url': '/login/'}),
    (r'^passwordChange/', 'django.contrib.auth.views.password_change', {'template_name': 'password_change_form.html'}),
    (r'^passwordChangeDone/', 'django.contrib.auth.views.password_change_done', {'template_name': 'password_change_success.html'}),
    (r'^passwordReset/', 'django.contrib.auth.views.password_reset', {'template_name': 'password_reset.html'}),
    (r'^passwordResetDone/', 'django.contrib.auth.views.password_reset_done', {'template_name': 'password_reset_done.html'}),
    (r'^passwordResetConfirm/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$', 'django.contrib.auth.views.password_reset_confirm',
        {'template_name': 'password_reset_confirm.html'}),
    (r'^passwordResetComplete/', 'django.contrib.auth.views.password_reset_complete', {'template_name': 'password_reset_complete.html'}),


)
