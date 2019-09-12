# Generated by Django 2.2.5 on 2019-09-12 13:59

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Flat',
            fields=[
                ('flat_id', models.IntegerField(primary_key=True, serialize=False)),
                ('price', models.FloatField()),
                ('views_count', models.IntegerField()),
                ('floor', models.IntegerField()),
                ('floors_amount', models.IntegerField(null=True)),
                ('building_type', models.CharField(max_length=120)),
                ('rooms', models.CharField(max_length=120)),
                ('decoration', models.CharField(max_length=120)),
                ('square', models.FloatField()),
                ('living_square', models.FloatField(null=True)),
                ('kitchen_square', models.FloatField(null=True)),
                ('scraped_date', models.DateTimeField(default=None)),
                ('finish_date', models.CharField(max_length=120, null=True)),
                ('url', models.URLField()),
                ('district1', models.CharField(default=None, max_length=100, null=True)),
                ('district2', models.CharField(default=None, max_length=100, null=True)),
                ('district3', models.CharField(default=None, max_length=100, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Page',
            fields=[
                ('number', models.IntegerField(primary_key=True, serialize=False)),
            ],
        ),
        migrations.CreateModel(
            name='Proxy',
            fields=[
                ('ip', models.CharField(max_length=70, primary_key=True, serialize=False)),
            ],
        ),
    ]
