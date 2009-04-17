from django.contrib.sitemaps import Sitemap
from models import Entry

class BlogSitemap(Sitemap):
    changefreq = "never"
    priority = 0.5

    def items(self):
        return Entry.public.all()

    def lastmod(self, obj):
        return obj.published
