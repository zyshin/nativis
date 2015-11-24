from django.conf.urls import include, url
# from django.contrib import admin

urlpatterns = [
    # Examples:
    # url(r'^$', 'proxyserver.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    # url(r'^admin/', include(admin.site.urls)),
    url(r'^proxy/', 'proxyhandler.views.proxy'),
    url(r'^evaluate/', 'proxyhandler.views.evaluate'),
]
