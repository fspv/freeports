from django.conf.urls.defaults import patterns, include, url
from freeports.views import big_swmap
from freeports.views import switch, port, admin, admin_swlist,admin_reservelist,admin_reservedel,admin_reserverestore,admin_reserveadd,admin_swadd,admin_swadd,admin_swdel,admin_swrestore,swinfo,swedit,comments,comment_add,comment_delete,comment_edit,ext_map,ext_map_sector,faq,search
# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'freeports.views.home', name='home'),
    # url(r'^freeports/', include('freeports.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
    ('^$',big_swmap),
    ('^search/{0,1}$',search),
    ( r'^accounts/login/$', 'django.contrib.auth.views.login'),
    ( r'^accounts/logout/$', 'django.contrib.auth.views.logout_then_login' ),
    ('^switch-([0-9]*)/{0,1}$',switch),
    ('^switch-(?P<switch>\d{1,6})/port-(?P<port>\d{1,2})/{0,1}$',port),
    ('^switch-([0-9]*)/info/{0,1}$',swinfo),
    ('^switch-([0-9]*)/edit/{0,1}$',swedit),
    ('^switch-([0-9]*)/comments/{0,1}$',comments),
    ('^switch-([0-9]*)/comments/add/{0,1}$',comment_add),
    ('^switch-(?P<switch>\d{1,6})/comments/(?P<comment>\d{1,6})/delete/{0,1}$',comment_delete),
    ('^switch-(?P<switch>\d{1,6})/comments/(?P<comment>\d{1,6})/edit/{0,1}$',comment_edit),
    ('^accounts/profile/{0,1}$',admin),
    ('^admin/{0,1}$',admin),
    ('^admin/switches/{0,1}$',admin_swlist),
    ('^admin/reserves/{0,1}$',admin_reservelist),
    ('^admin/switches/add/{0,1}$',admin_swadd),
    ('^admin/switches/(?P<switch>\d{1,6})/delete/{0,1}$',admin_swdel),
    ('^admin/switches/(?P<switch>\d{1,6})/restore/{0,1}$',admin_swrestore),
    ('^admin/reserves/(?P<reserveid>\d{1,6})/delete/{0,1}$',admin_reservedel),
    ('^admin/reserves/(?P<reserveid>\d{1,6})/restore/{0,1}$',admin_reserverestore),
    ('^admin/switches/add/{0,1}$',admin_swadd),
    ('^admin/reserves/add/{0,1}$',admin_reserveadd),
    ('^extended/{0,1}$',ext_map),
    ('^extended/([GDEJ]{1,1})/{0,1}$',ext_map_sector),
    ('^faq/{0,1}$',faq)
)
