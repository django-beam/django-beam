from django.db import models


class Dragonfly(models.Model):
    name = models.CharField(max_length=255)
    age = models.IntegerField()

    def __str__(self):
        return self.name


class Petaluridae(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name
