from django.db import models
from django.utils import timezone

class ScrapingJob(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('running', 'Em Execução'),
        ('completed', 'Concluído'),
        ('failed', 'Falhou'),
    ]

    url = models.URLField(max_length=500)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Scraping Job - {self.url} ({self.status})"

class ScrapedData(models.Model):
    job = models.ForeignKey(ScrapingJob, on_delete=models.CASCADE, related_name='scraped_data')
    title = models.CharField(max_length=200, null=True, blank=True)
    content = models.TextField(null=True, blank=True)
    metadata = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Scraped Data - {self.title or 'Untitled'}"
