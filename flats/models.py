from django.db import models
from django.utils import timezone
from datetime import datetime


class Flat(models.Model):
    flat_id = models.IntegerField(primary_key=True)
    price = models.FloatField()
    views_count = models.IntegerField()
    floor = models.IntegerField()
    floors_amount = models.IntegerField(null=True)
    building_type = models.CharField(max_length=13)
    rooms = models.CharField(max_length=19)
    decoration = models.CharField(max_length=14)
    square = models.FloatField()
    living_square = models.FloatField(null=True)
    kitchen_square = models.FloatField(null=True)
    scraped_date = models.DateTimeField(default=None, null=True)
    finish_date = models.CharField(max_length=18, null=True)
    url = models.URLField()
    district1 = models.CharField(null=True, max_length=25, default=None)
    district2 = models.CharField(null=True, max_length=25, default=None)
    district3 = models.CharField(null=True, max_length=25, default=None)
    region = models.CharField(null=True, max_length=16, default=None)

    latitude = models.FloatField(null=True, default=None, blank=True)
    longitude = models.FloatField(null=True, default=None, blank=True)

    def __str__(self):
        return f'Район: {self.district1} | rooms: {self.rooms} | Updated : {self.scraped_date}'


class Page(models.Model):
    number = models.IntegerField(primary_key=True)

    def __str__(self):
        return str(self.number)


class Proxy(models.Model):
    ip = models.CharField(max_length=70, primary_key=True)

    def __str__(self):
        return self.ip
