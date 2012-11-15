from django.conf.urls import patterns, include, url
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
    (r'^login/$', 'projectApp1.views.siteLogin'),
    (r'^logout/$', 'django.contrib.auth.views.logout_then_login', {'login_url': '/login/'}),
    (r'^createUser/', 'projectApp1.views.createUser'),
    (r'^passwordChange/', 'django.contrib.auth.views.password_change'),
    (r'^passwordChangeDone/', 'django.contrib.auth.views.password_change_done'),
    (r'^passwordReset/', 'django.contrib.auth.views.password_reset'),
    (r'^passwordResetDone/', 'django.contrib.auth.views.password_reset_done'),
    (r'^passwordResetConfirm/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$', 'django.contrib.auth.views.password_reset_confirm'),
    (r'^passwordResetComplete/', 'django.contrib.auth.views.password_reset_complete'),
    (r'^home/$', 'projectApp1.views.home'),
)
