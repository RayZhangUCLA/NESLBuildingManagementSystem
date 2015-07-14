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

class Room(models.Model):
	room_name = models.CharField(max_length=100)

	def __str__(self):
		return self.room_name

class Room_Tabs(models.Model):
	room = models.ForeignKey(Room)
	tabs = models.CharField(max_length=1000)

	def __str__(self):
		return self.tabs

class Room_PageUUIDs(models.Model):
	room = models.ForeignKey(Room)
	Power = models.CharField(max_length=2000)
	Water = models.CharField(max_length=2000)
	Gas = models.CharField(max_length=2000)
	Environment = models.TextField() #In the order of Indoor: Temp, Humidity, Pressure, Co2, Sound; Outdoor:Temp, Humidity
	Motion = models.TextField() #???Maybe in the order of graphs shown on webpage

	def __str__(self):
		return 'Cooming soom'

class Room_Sensorlist(models.Model):
	room = models.ForeignKey(Room)
	sensor_list_tree = models.TextField()

	def __str__(self):
		return self.sensor_list_tree
   