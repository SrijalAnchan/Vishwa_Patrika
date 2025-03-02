from django.contrib import admin
from .models import NewsArticle

@admin.register(NewsArticle)
class NewsArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'source', 'category', 'created_at', 'updated_at')
    list_filter = ('source', 'category', 'created_at')
    search_fields = ('title', 'content')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'content', 'author')
        }),
        ('Source Information', {
            'fields': ('source', 'category', 'url', 'image')
        }),
        ('Metadata', {
            'fields': ('api_source_id', 'created_at', 'updated_at')
        }),
    )
