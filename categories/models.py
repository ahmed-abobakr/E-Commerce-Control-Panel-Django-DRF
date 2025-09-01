from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=100)
    parent_id = models.IntegerField(null=True)
    
    def __str__(self):
        return self.name
