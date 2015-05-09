from django.db import models

# Create your models here.
class Menu_Tree(models.Model):
    tree_id = models.IntegerField()
    tree = models.TextField()

class Path_UUID(models.Model):
    path = models.CharField(max_length=1000)
    uuid = models.CharField(max_length=100)
    data_type = models.IntegerField(default=0) #0 for continous, 1 for discrete

    def __str__(self):
        return self.path + "|" + self.uuid

