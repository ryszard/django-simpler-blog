from django.db import models
from django.contrib.auth.models import User
import tagging
import tagging.fields
from comment_utils.moderation import AkismetModerator, moderator, AlreadyModerated
import akismet as akismet
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext_lazy as _

# Create your models here.

ENTRIES_SORT_CHOICES = (('title', 'Alphabetical (A-Z)'),
                        ('-published', 'newest first'),
                        ('published', 'oldest first'),)


class Category(models.Model):
    name = models.CharField(_('name'), max_length='200')
    slug = models.SlugField(max_length='200')
    description = models.TextField(_('description'), blank=True)
    entries_ordering = models.CharField(_('entries ordering'), max_length='50', choices=ENTRIES_SORT_CHOICES, default='-published')
    image = models.ImageField(_('image'), upload_to='uploads/category/')

    def __init__(self, *args, **kwargs):
        super(Category, self).__init__(*args, **kwargs)
        if not self.slug:
            self.slug = slugify(self.name)
        if not self.entries_ordering:
            self.entries_ordering = u'-published'
    @property
    def entry_for_preview(self):
        """Returns the last entry in this category that is not on the front
        page. Right now the number of entries on the front page is
        hardcoded (1). If this is for some reason impossible (not
        enough entries, etc.), then it returns None.

        >>> from django.core import management

        >>> management.call_command('loaddata', 'two_categories.json', verbosity=0)

        >>> a = Category.objects.get(name='a')

        >>> b = Category.objects.get(name='b')

        >>> def add_entry(category, pub_date):
        ...     e = Entry(author = User.objects.get(id=1),
        ...               category = category,
        ...               published = pub_date,
        ...               draft = False,
        ...               title = "%s %s" % (category.name, pub_date),
        ...               body = 'foo',
        ...               slug = "%s-%s" %(category.name, pub_date))
        ...     e.save()
        ...     return e
        ...

        >>> add_entry(a, '2008-11-01')
        <Entry: ...>

        >>> a.entry_for_preview

        >>> b.entry_for_preview

        >>> add_entry(b, '2008-11-02')
        <Entry: ...>

        >>> Entry.public.latest()
        <Entry: b ...>

        >>> a.entry_for_preview
        <Entry: a 2008-11-01>

        >>> b.entry_for_preview

        >>> add_entry(b, '2008-11-03')
        <Entry: ...>

        >>> a.entry_for_preview
        <Entry: a 2008-11-01>

        >>> b.entry_for_preview
        <Entry: b 2008-11-02>

        >>> last_b = add_entry(b, '2008-11-04')

        >>> last_a = add_entry(a, '2008-11-05')

        >>> b.entry_for_preview
        <Entry: b 2008-11-04>

        >>> last_b.draft = True

        >>> last_b.save()

        >>> last_b.draft
        True

        >>> b.entry_for_preview
        <Entry: b 2008-11-03>

        >>> last_a.delete()

        >>> last_b.delete()


        """

        try:
            last = Entry.public.latest()
        except Entry.DoesNotExist:
            # no entries at all
            return None

        try:
            try:
                cat_last, cat_penultimate = self.entries_set_orig.filter(draft=False).order_by('-published')[:2]
            except ValueError: # there is less than two entries in this category
                if last in self.entries_set:
                    return None
                else:
                    return self.entries_set[0]
        except IndexError:
            # no entries in category
            return None

        if cat_last == last:
            return cat_penultimate
        else:
            return cat_last


    @property
    def entries_set(self, *args):
        "List of related entries that aren't drafts, in the appropriate order."
        return self.entries_set_orig.filter(draft=False).order_by(self.entries_ordering)

    @models.permalink
    def get_absolute_url(self):
        return ('category', (), {'slug': self.slug})

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name_plural = _('Categories')
        verbose_name = _('Category')

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
    category = models.ForeignKey(Category, related_name='entries_set_orig')
    published = models.DateTimeField(_('publication date'))
    draft = models.BooleanField(_('if checked this entry will be a draft and will not be published'), default=True)
    image_for_preview_orig = models.ImageField(_(u'image for preview'), upload_to='uploads/%Y/%m/', null=True, blank=True)
    last_modified = models.DateTimeField(_(u'date modified'), auto_now=True)
    title = models.CharField(max_length='200', unique_for_date='published')
    slug = models.SlugField(max_length='200')
    body = models.TextField()
    tags = tagging.fields.TagField()
    objects = models.Manager()
    public = PublishedEntriesManager()

    @models.permalink
    def get_absolute_url(self):
        return ('blog-entry', (), dict(year=self.published.year, month=self.published.month, day=self.published.day, slug=self.slug))

    @property
    def image_for_preview(self):
        return self.image_for_preview_orig or self.category.image

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

try:
    moderator.register(Entry, AkismetModerator)
except AlreadyModerated:
    pass

class Image(models.Model):
    entry = models.ForeignKey(Entry)
    date = models.DateField(auto_now_add=True)
    image = models.ImageField(upload_to='uploads/%Y/%m/')

    class Meta:
        verbose_name = _('Image')
        verbose_name_plural = _('Images')

