from django.contrib import admin
from .models import Tag

class TagAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    list_display = ('name', 'slug')

admin.site.register(Tag, TagAdmin)
