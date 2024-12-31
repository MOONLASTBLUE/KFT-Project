from django.db import models

# Create your models here.
class User(models.Model):
    name = models.CharField(max_length=100)
    preferences = models.TextField(null=True, blank=True)

class BehaviorTracking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event_type = models.CharField(max_length=50)
    event_details = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)