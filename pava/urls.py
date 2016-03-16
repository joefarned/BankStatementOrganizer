from django.conf.urls import patterns, include, url
from django.core.urlresolvers import reverse_lazy

# Uncomment the next two lines to enable the admin:
from django.contrib import admin

urlpatterns = patterns('',
    url(r'^$', 'pava.core.views.home', name='home'),
    url(r'^privacy$', 'pava.core.views.privacy', name='privacy'),
    url(r'^terms$', 'pava.core.views.terms', name='privacy'),
    url(r'^feed$', 'pava.core.views.feed', name='feed'),
    url(r'^accounts$', 'pava.core.views.accounts', name='accounts'),
    url(r'^accounts/new$', 'pava.core.views.new_account', name='new_account'),
    url(r'^accounts/new/step$', 'pava.core.views.new_account_mfa', name='new_account_step'),

    url(r'^load$', 'pava.core.views.load_data', name='load_data'),
    url(r'^api/', include('pava.api.urls')),

    url(r'^login$', 'django.contrib.auth.views.login',name="login"),
    url(r'^logout$', 'django.contrib.auth.views.logout', {"next_page" : reverse_lazy('login')}, name="logout"),

    (r'^accounts/', include('registration.backends.default.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)
