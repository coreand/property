# Generated by Django 2.2.5 on 2019-09-12 14:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('flats', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='flat',
            name='region',
            field=models.CharField(default=None, max_length=100, null=True),
        ),
    ]
