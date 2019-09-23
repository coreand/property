from django.contrib import admin
from flats.models import Flat, Page


class FlatAdmin(admin.ModelAdmin):
    list_display = [
        'flat_id',
        'price',
        'views_count',

    ]

    search_fields = [
        'flat_id', 'price', 'views_count', 'region'
    ]


admin.site.register(Page)
admin.site.register(Flat, FlatAdmin)


