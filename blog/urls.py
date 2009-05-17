from django.conf.urls.defaults import *
from django.conf import settings
from models import Entry, Category
from views import tag_entry_detail_view, category_detail_view, preview, post_comment
from feeds import LatestEntries
from comment_utils.views import this_is_akismet_ham, this_is_akismet_spam

urlpatterns = patterns('',
                       url(r'^admin/blog/entry/(?P<object_id>\d+)/preview/$', preview),

                       url(r'^admin/akismet-spam/comment/(?P<id>\d+)$', this_is_akismet_spam, name='akismet-comment-spam'),
                       url(r'^admin/akismet-ham/comment/(?P<id>\d+)$', this_is_akismet_ham, name='akismet-comment-ham'),

                       url(r'blog/tag/(?P<slug>[\w\-]+)', tag_entry_detail_view, name='blog-tag'),
                       url(r'^category/(?P<slug>[\w\-]+)', category_detail_view, name='blog-category'),
                       url(r'^feed/(?P<url>.*)/?$', 'django.contrib.syndication.views.feed', {'feed_dict': {'latest': LatestEntries}}, name='blog-feed'),

                       url(r'^comments/post/$', post_comment, name='comments-post-comment'),
                       )

urlpatterns += patterns('django.views.generic',
                        url('^$', 'list_detail.object_list', dict(queryset=Entry.public.order_by('-published'), paginate_by=getattr(settings, 'SET_DETAILS_ENTRIES_PER_PAGE', 3)), name='blog-index'),
                        url(r'^(?P<year>\d{4})/(?P<month>\d{1,2})/(?P<day>\d{1,2})/(?P<slug>[\w\-]+)/?$',
                            'date_based.object_detail', dict(queryset=Entry.public.all(), month_format='%m', date_field='published'), name='blog-entry'),
)

