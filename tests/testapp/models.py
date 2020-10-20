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


class Sighting(models.Model):
    name = models.CharField(max_length=255)
    dragonfly = models.ForeignKey(Dragonfly, on_delete=models.SET_NULL, null=True)

    created_at = models.DateTimeField(auto_now_add=True)


class ProtectedSighting(models.Model):
    name = models.CharField(max_length=255)
    dragonfly = models.ForeignKey(Dragonfly, on_delete=models.PROTECT)

    created_at = models.DateTimeField(auto_now_add=True)


class CascadingSighting(models.Model):
    name = models.CharField(max_length=255)
    dragonfly = models.ForeignKey(Dragonfly, on_delete=models.CASCADE)

    created_at = models.DateTimeField(auto_now_add=True)
