from django.contrib.auth.models import User
from django.db import models

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profession = models.CharField(max_length=50)

    def __str__(self):
        return self.user.username

class Submission(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submissions')
    input_text = models.TextField(blank=True, default='')
    uploaded_file_name = models.CharField(max_length=255, blank=True, default='')
    result = models.CharField(max_length=100)
    similarity_percentage = models.FloatField()
    possible_sources = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.created_at}"
