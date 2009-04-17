from django.contrib.syndication.feeds import Feed
from models import Entry
from django.conf import settings

class LatestEntries(Feed):
    title = settings.BLOG_TITLE
    link = "/"
    description = settings.BLOG_SUBTITLE

    def items(self):
        return Entry.public.order_by('-published')[:5]
