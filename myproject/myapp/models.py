from django.db import models
from django.utils import timezone 

# Create your models here.
class Drink(models.Model):
    name = models.CharField(max_length=100)
    flavor_tags = models.TextField(default="Default Flavor Tag")
    customizable_sweetness = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class User(models.Model):
    user_id = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Feedback(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.CharField(max_length=100, default='DefaultCategory') 
    base_type = models.CharField(max_length=100)
    selected_tags = models.TextField(default='Default Tag') 
    recommendation = models.CharField(max_length=255, default='Default Recommendation') 
    rating = models.IntegerField(null=True, blank=True)  
    created_at = models.DateTimeField(default=timezone.now)

