from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

from utilities.models import AutoSlugField
# Create your models here.


class PublishedEntriesManager(models.Manager):
    def get_query_set(self):
        return super(PublishedEntriesManager, self).get_query_set().filter(draft=False)

class Entry(models.Model):
    """
    Blog entries.

    The manager to get published entries is Entry.public:

    >>> [e.draft for e in Entry.public.all()]
    [False, False, False]
    """
    author = models.ForeignKey(User)
    published = models.DateTimeField(_('publication date'))
    draft = models.BooleanField(_('if checked this entry will be a draft and will not be published'), default=True)
    last_modified = models.DateTimeField(_(u'date modified'), auto_now=True)
    title = models.CharField(max_length='200', unique_for_date='published')
    slug = AutoSlugField(max_length='200')
    body = models.TextField()
    objects = models.Manager()
    public = PublishedEntriesManager()

    @models.permalink
    def get_absolute_url(self):
        return ('blog-entry', (), dict(year=self.published.year, month=self.published.month, day=self.published.day, slug=self.slug))

    @property
    def next(self):
        """
        The next (in terms of `published') entry that is not a
        draft. Next in this case means added *later*. None if this
        entry is the last one.

        >>> entries = Entry.public.order_by('-published')

        >>> entries
        [<Entry: b 2008-11-03>, <Entry: b 2008-11-02>, <Entry: a 2008-11-01>]

        >>> entries[0].previous
        <Entry: b 2008-11-02>

        >>> entries[0].next

        >>> draft = entries[0].previous

        >>> draft.draft = True

        >>> draft.save()

        >>> draft.draft
        True

        >>> entries[0].previous
        <Entry: a 2008-11-01>

        >>> entries[0].previous.previous

        """
        try:
            return self.get_next_by_published(draft=False)
        except self.DoesNotExist:
            return None

    @property
    def previous(self):
        """
        The previous (in terms of `published') entry that is not a
        draft. Previous in this case means added *before*. None is
        this entry is the first one.
        """
        try:
            return self.get_previous_by_published(draft=False)
        except self.DoesNotExist:
            return None

    def __unicode__(self):
        return self.title

    class Meta:
        verbose_name_plural = _('Entries')
        verbose_name = _('Entry')
        get_latest_by = 'published'

class Image(models.Model):
    entry = models.ForeignKey(Entry)
    date = models.DateField(auto_now_add=True)
    image = models.ImageField(upload_to='uploads/%Y/%m/')

    class Meta:
        verbose_name = _('Image')
        verbose_name_plural = _('Images')

