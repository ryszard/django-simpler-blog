from models import Entry, Image
from django.contrib import admin

class ImageInline(admin.StackedInline):
    model = Image


class EntryAdmin(admin.ModelAdmin):
    list_display = ('title', 'last_modified')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ImageInline,]

admin.site.register(Entry, EntryAdmin)


