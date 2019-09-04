from django.db import models


class Flat(models.Model):
    flat_id = models.IntegerField(primary_key=True)
    price = models.FloatField()
    views_count = models.IntegerField()
    floor = models.IntegerField()
    floors_amount = models.IntegerField(null=True)
    building_type = models.CharField(max_length=120)
    rooms = models.CharField(max_length=120)
    decoration = models.CharField(max_length=120)
    square = models.FloatField()
    living_square = models.FloatField(null=True)
    kitchen_square = models.FloatField(null=True)
    finish_date = models.CharField(max_length=120, null=True)
    url = models.URLField()

    def __str__(self):
        return f'Цена: {self.price} | Комнаты: {self.rooms}'


class Page(models.Model):
    number = models.IntegerField(primary_key=True)

    def __str__(self):
        return str(self.number)


class Proxy(models.Model):
    ip = models.CharField(max_length=70, primary_key=True)

    def __str__(self):
        return self.ip
