from models import Entry, Category, Image
from django.contrib import admin

class ImageInline(admin.StackedInline):
    model = Image


class EntryAdmin(admin.ModelAdmin):
    list_display = ('title', 'last_modified')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ImageInline,]

class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}

admin.site.register(Entry, EntryAdmin)
admin.site.register(Category, CategoryAdmin)

