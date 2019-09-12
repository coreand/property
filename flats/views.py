from django.shortcuts import render
from flats.models import Flat
from django.views.generic import View
from flats.forms import FilterForm
from django.shortcuts import render, get_object_or_404, redirect
from scrape.scrape.spiders.avito import get_avg_price


class HomeView(View):
    def get(self, *args, **kwargs):
        form = FilterForm
        context = {
            'form': form,
        }
        return render(self.request, 'home.html', context)

    def post(self, *args, **kwargs):
        form = FilterForm(self.request.POST or None)
        if form.is_valid():
            building_type = form.cleaned_data.get(
                'building_type')
            rooms = form.cleaned_data.get(
                'rooms')
            floor = form.cleaned_data.get(
                'floor')
            floors_amount = form.cleaned_data.get(
                'floors_amount')
            district = form.cleaned_data.get(
                'district')
            region = form.cleaned_data.get(
                'region')

            params = {}
            if building_type != 'NotSpecified':
                params['building_type'] = building_type
            if rooms != 'NotSpecified':
                params['rooms'] = rooms
            if floor != '':
                params['floor'] = floor
            if floors_amount != '':
                params['floors_amount'] = floors_amount
            if district != 'NotSpecified':
                params['district1'] = district
            if region != 'NotSpecified':
                params['region'] = region

            avg_price, flats_amount = get_avg_price(**params)
            print(avg_price, flats_amount)
            # print(building_type)
            # print(rooms)
            # print(floor)
            # print(floors_amount)
            # print(district)
            # print(region)
        context = {
            'form': form,
            'avg_price': avg_price,
            'flats_amount': flats_amount,
        }
        # return redirect('flats:home-page')
        return render(self.request, 'home.html', context)
