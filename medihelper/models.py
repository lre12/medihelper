from django.db import models

# Create your models here.
class medicine(models.Model):
	name = models.CharField(max_length=50)
	maker = models.CharField(max_length=50)
	information = models.TextField()
	danger = models.TextField()
	score = models.IntegerField()

	class Meta:
		ordering = ['-score']

	def __str__(self):
		return self.name