# Create your views here.
from tagging.models import TaggedItem, Tag
from models import Entry, Category
from django.views.generic.list_detail import object_list, object_detail
from django.contrib.comments.views.comments import CommentPostBadRequest, comment_done
from django.conf import settings
from django.db import models
from django.utils.html import escape
from django.http import HttpResponseRedirect
from django.http import Http404
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_POST
from django.contrib import comments
from django.contrib.comments import signals
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.comments.views.utils import next_redirect

def tag_entry_detail_view(request, slug, *args, **kwargs):
    tag = Tag.objects.get(slug=slug)
    queryset = TaggedItem.objects.get_by_model(Entry, tag).filter(draft=False).all()
    try:
        kwargs['extra_context']['tag'] = tag
    except KeyError:
        kwargs['extra_context'] = {'tag': tag}
    queryset._clone = lambda: queryset
    return object_list(request, queryset, template_name='blog/tag_detail.html',
                       paginate_by=settings.SET_DETAILS_ENTRIES_PER_PAGE,
                       *args, **kwargs)

def category_detail_view(request, slug, *args, **kwargs):
    try:
        category = Category.objects.select_related().get(slug=slug)
    except Category.DoesNotExist:
        raise Http404
    queryset = category.entries_set
    try:
        kwargs['extra_context']['category'] = category
    except KeyError:
        kwargs['extra_context'] = {'category': category}

    if category.entries_ordering != 'title':
        kwargs['paginate_by'] = settings.SET_DETAILS_ENTRIES_PER_PAGE

    return object_list(request, queryset, template_name='blog/category_detail.html', *args, **kwargs)

@staff_member_required
def preview(request, object_id):
   return object_detail(request, object_id=object_id, queryset=Entry.objects.all())

# def my_post_comment(request):
#     try:
#         next = request.POST['next']
#     except KeyError:
#         next = request.GET['next']
#     return post_comment(request, next=next)

# Copy and Paste to the resque. Let's just hope
# django.contrib.comments gets some love in the next release.

@require_POST
def post_comment(request, next=None):
    """
    Post a comment.

    HTTP POST is required. If ``POST['submit'] == "preview"`` or if there are
    errors a preview template, ``comments/preview.html``, will be rendered.
    """
    # get a sensible value for next
    next = next or request.POST.get('next') or request.GET.get('next')

    # Fill out some initial data fields from an authenticated user, if present
    data = request.POST.copy()
    if request.user.is_authenticated():
        if not data.get('name', ''):
            data["name"] = request.user.get_full_name() or request.user.username
        if not data.get('email', ''):
            data["email"] = request.user.email

    # Look up the object we're trying to comment about
    ctype = data.get("content_type")
    object_pk = data.get("object_pk")
    if ctype is None or object_pk is None:
        return CommentPostBadRequest("Missing content_type or object_pk field.")
    try:
        model = models.get_model(*ctype.split(".", 1))
        target = model._default_manager.get(pk=object_pk)
    except TypeError:
        return CommentPostBadRequest(
            "Invalid content_type value: %r" % escape(ctype))
    except AttributeError:
        return CommentPostBadRequest(
            "The given content-type %r does not resolve to a valid model." % \
                escape(ctype))
    except ObjectDoesNotExist:
        return CommentPostBadRequest(
            "No object matching content-type %r and object PK %r exists." % \
                (escape(ctype), escape(object_pk)))

    # Do we want to preview the comment?
    preview = "preview" in data

    # Construct the comment form
    form = comments.get_form()(target, data=data)

    # Check security information
    if form.security_errors():
        return CommentPostBadRequest(
            "The comment form failed security verification: %s" % \
                escape(str(form.security_errors())))

    # If there are errors or if we requested a preview show the comment
    if form.errors or preview:
        template_list = [
            "comments/%s_%s_preview.html" % tuple(str(model._meta).split(".")),
            "comments/%s_preview.html" % model._meta.app_label,
            "comments/preview.html",
        ]
        return render_to_response(
            template_list, {
                "next": target.get_absolute_url(), # sent next to the template
                "comment" : form.data.get("comment", ""),
                "form" : form,
            },
            RequestContext(request, {})
        )

    # Otherwise create the comment
    comment = form.get_comment_object()
    comment.ip_address = request.META.get("REMOTE_ADDR", None)
    if request.user.is_authenticated():
        comment.user = request.user

    # Signal that the comment is about to be saved
    responses = signals.comment_will_be_posted.send(
        sender  = comment.__class__,
        comment = comment,
        request = request
    )

    for (receiver, response) in responses:
        if response == False:
            return CommentPostBadRequest(
                "comment_will_be_posted receiver %r killed the comment" % receiver.__name__)

    # Save the comment and signal that it was saved
    comment.save()
    signals.comment_was_posted.send(
        sender  = comment.__class__,
        comment = comment,
        request = request
    )

    return next_redirect(data, next, comment_done, c=comment._get_pk_val())

