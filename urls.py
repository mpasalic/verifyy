from django.conf.urls.defaults import *
from django.contrib import admin
import settings

handler500 = 'djangotoolbox.errorviews.server_error'

urlpatterns = patterns('',
	
    (r'^$', 'main.views.index'),
	(r'^/$', 'main.views.index'),
	(r'^login$', 'main.views.login'),
	(r'^logout$', 'main.views.logout'),
	(r'^register$', 'main.views.register'),
	(r'^search$', 'main.views.search'),
    (r'^authCheck$', 'main.views.authCheck'),
    (r'^msg$', 'main.views.msg'),
    (r'^view/(?P<exp_id>\d+)/$', 'main.views.experiment'),
	(r'^edit/(?P<exp_id>\d+)/$', 'main.views.edit'),
    (r'^postcomm/(?P<exp_id>\d+)/$', 'main.views.postcomm'),
	(r'^data/(?P<exp_id>\d+)/$', 'main.views.data'),
	(r'^submit/(?P<exp_id>\d+)/$', 'main.views.submit'),
	(r'^join/(?P<exp_id>\d+)/$', 'main.views.join'),
	(r'^unjoin/(?P<exp_id>\d+)/$', 'main.views.unjoin'),
	(r'^upvote/(?P<exp_id>\d+)/$', 'main.views.upvote'),
	(r'^downvote/(?P<exp_id>\d+)/$', 'main.views.downvote'),
	(r'^user/(?P<username>[a-zA-Z0-9_]+)/$', 'main.views.user'),
	(r'^friends/$', 'main.views.friends'),
    (r'^new$', 'main.views.new_experiment'),
    (r'^create$', 'main.views.create_experiment'),
    (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root':  settings.STATIC_DOC_ROOT}),
	(r'^admin/', include(admin.site.urls)),
)
