from django.db import models
from django.contrib.auth import get_user_model

class NewsArticle(models.Model):
    CATEGORY_CHOICES = [
        ('POL', 'Politics'),
        ('TECH', 'Technology'), 
        ('BUS', 'Business'),
        ('SPO', 'Sports'),
        ('ENT', 'Entertainment')
    ]

    SOURCE_CHOICES = [
        ('BBC', 'BBC News'),
        ('REU', 'Reuters'),
        ('TH', 'The Hindu'),
        ('WION', 'WION'),
        ('TOI', 'The Times of India'),  
        ('NDTV', 'NDTV'), 
    ]

    title = models.CharField(max_length=255)
    content = models.TextField()
    author = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    source = models.CharField(max_length=50, choices=SOURCE_CHOICES, default='BBC')
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='POL')

    url = models.URLField(default='https://example.com')
    image = models.ImageField(upload_to='news_images/', blank=True, null=True)
    api_source_id = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.source})"
    
