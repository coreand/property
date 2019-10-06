from django.forms import model_to_dict
from django.shortcuts import render
from flats.models import Flat
from django.views.generic import View
from flats.forms import FilterForm
from django.shortcuts import render, get_object_or_404, redirect
from scrape.scrape.spiders.avito import get_avg_price
import math


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
            coors = form.cleaned_data.get(
                'coors')
            building_type = form.cleaned_data.get(
                'building_type')
            rooms = form.cleaned_data.get(
                'rooms')
            floor = form.cleaned_data.get(
                'floor')
            floors_amount = form.cleaned_data.get(
                'floors_amount')
            region = form.cleaned_data.get(
                'region')

            district = form.cleaned_data.get(
                'district')
            moscow_stations = form.cleaned_data.get(
                'moscow_stations')
            spb_stations = form.cleaned_data.get(
                'spb_stations')

            square_min = form.cleaned_data.get(
                'square_min')
            square_max = form.cleaned_data.get(
                'square_max')

            params = {}
            if building_type != 'NotSpecified':
                params['building_type'] = building_type
            if rooms != 'NotSpecified':
                params['rooms'] = rooms
            if floor != '':
                params['floor'] = floor
            if floors_amount != '':
                params['floors_amount'] = floors_amount
            if region != 'NotSpecified':
                params['region'] = region
            if square_min != '':
                params['square'] = [square_min, square_max]

            if square_max != '':
                params['square'] = [square_min, square_max]

            if region == 'mahachkala':
                if district != 'NotSpecified':
                    params['district1'] = district
            if region == 'moskva':
                if moscow_stations != 'NotSpecified':
                    params['district1'] = moscow_stations
            if region == 'sankt-peterburg':
                if spb_stations != 'NotSpecified':
                    params['district1'] = spb_stations

            coors_nearby_flats = []
            ids = []

            if coors:
                cur_lat, cur_long = float(coors.split(', ')[0]), float(coors.split(', ')[1])
                flats_with_coors = Flat.objects.exclude(longitude=None)

                for flat in flats_with_coors:
                    if calc_coors(cur_lat, cur_long, flat.longitude, flat.latitude,) < 0.007:
                        coors_nearby_flats.append(flat)
                        print(model_to_dict(flat))
                        ids.append(flat.flat_id)
                print(coors_nearby_flats)
                nearby_flats = Flat.objects.filter(pk__in=ids)

                total_price = 0
                square = params.pop('square', None)

                if square is not None:
                    if square[0] is None:
                        square[0] = 0
                    if square[1] is None:
                        square[1] = math.inf
                if square:
                    nearby_flats = nearby_flats.filter(**params, square__range=square)
                else:
                    nearby_flats = nearby_flats.filter(**params)

                for item in nearby_flats:
                    print(item.latitude)
                    print(item.longitude)

                for flatt in nearby_flats:
                    total_price += flatt.price
                avg_price, flats_amount = int(int(total_price) / len(nearby_flats)), len(
                    nearby_flats)

                context = {
                    'form': form,
                    'avg_price': avg_price,
                    'flats_amount': flats_amount,
                }

                return render(self.request, 'home.html', context)
            avg_price, flats_amount = get_avg_price(**params)
            context = {
                'form': form,
                'avg_price': avg_price,
                'flats_amount': flats_amount,
            }

            return render(self.request, 'home.html', context)
        return render(self.request, 'home.html')


def calc_coors(cur_lat, cur_long, flat_lat, flat_long):
    distance = math.sqrt(pow((cur_lat - flat_lat), 2) + pow((cur_long - flat_long), 2))
    return distance
