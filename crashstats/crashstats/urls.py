from django.conf.urls.defaults import patterns, url
from django.views.generic.simple import redirect_to
from django.conf import settings

from . import views

products = r'^products/(?P<product>\w+)'
versions = r'/versions/(?P<versions>[;\w\.()]+)'
days = r'/days/(?P<days>\d+)'
crash_type = r'/crash_type/(?P<crash_type>\w+)'
os_name = r'/os_name/(?P<os_name>[\w\s]+)'

urlpatterns = patterns('',
    url(products + '/$',
        views.products,
        name='crashstats.products'),
    url(products + versions + '/$',
        views.products,
        name='crashstats.products'),
    url(products + '/topcrasher/byversion$',
        views.topcrasher,
        name='crashstats.topcrasher'),
    url(products + versions + '/topcrasher/byversion$',
        views.topcrasher,
        name='crashstats.topcrasher'),
    url(products + versions + days 
          + '/topcrasher/byversion$',
        views.topcrasher,
        name='crashstats.topcrasher'),
    url(products + versions + days + crash_type
          + '/topcrasher/byversion',
        views.topcrasher,
        name='crashstats.topcrasher'),
    url(products + versions + days + crash_type
          + os_name + '/topcrasher/byos',
        views.topcrasher,
        name='crashstats.topcrasher'),
    url(products + '/daily$',
        views.daily,
        name='crashstats.daily'),
    url(products + versions + '/daily$',
        views.daily,
        name='crashstats.daily'),
    url(products + '/builds$',
        views.builds,
        name='crashstats.builds'),
    # note the deliberate omission of the ';' despite calling the regex variable 'versionS'
    url(products + '/versions/(?P<versions>[\w\.()]+)' + '/builds$',
        views.builds,
        name='crashstats.builds'),
    url(products + '/builds.rss$',
        views.BuildsRss(),
        name='crashstats.buildsrss'),
    url(products + versions + '/builds.rss$',
        views.BuildsRss(),
        name='crashstats.buildsrss'),
    url(products + '/hangreport$',
        views.hangreport,
        name='crashstats.hangreport'),
    url(products + versions + '/hangreport$',
        views.hangreport,
        name='crashstats.hangreport'),
    url(products + '/topchangers$',
        views.topchangers,
        name='crashstats.topchangers'),
    url(products + versions + '/topchangers$',
        views.topchangers,
        name='crashstats.topchangers'),
    url(products + versions + days + '/topchangers$',
        views.topchangers,
        name='crashstats.topchangers'),
    url(r'^report/list$',
        views.report_list,
        name='crashstats.report_list'),
    url(r'^report/index/(?P<crash_id>.*)$',
        views.report_index,
        name='crashstats.report_index'),
    url(r'^query/$',
        views.query,
        name='crashstats.query'),
    url(r'^query/query$',
        redirect_to, {'url': '/query/?',
                      'permanent': False,
                      'query_string': True}),
    url(r'^buginfo/bug', views.buginfo,
        name='crashstats.buginfo'),
    url(r'^topcrasher/plot_signature/(?P<product>\w+)/(?P<versions>[;\w\.()]+)/(?P<start_date>[0-9]{4}-[0-9]{2}-[0-9]{2})/(?P<end_date>[0-9]{4}-[0-9]{2}-[0-9]{2})/(?P<signature>.*)',
        views.plot_signature,
        name='crashstats.plot_signature'),
    url(r'^signature_summary/json_data$',
        views.signature_summary,
        name='crashstats.signature_summary'),
    # if we do a permanent redirect, the browser will "cache" the redirect and
    # it will make it very hard to ever change the DEFAULT_PRODUCT
    url(r'^$', redirect_to, {'url': '/products/%s' % settings.DEFAULT_PRODUCT,
                             'permanent': False}),
)
