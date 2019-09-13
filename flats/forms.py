from django import forms

BUILDING_TYPE = (
    ('NotSpecified', 'Не важно'),
    (' кирпичный ', 'Кирпичный'),
    (' панельный ', 'Панельный'),
    (' блочный ', 'Блочный'),
    (' монолитный ', 'Монолитный'),
    (' деревянный ', 'Деревянный'),
)

ROOMS = (
    ('NotSpecified', 'Не важно'),
    (' студии ', 'Студия'),
    (' своб. планировка ', 'Свободная планировка'),
    ('1', '1'),
    ('2', '2'),
    ('3', '3'),
    ('4', '4'),
    ('5', '5'),
    ('6', '6'),
    ('7', '7'),
    ('8', '8'),
    ('9', '9'),
    ('>9', '>9'),
)

CITIES = (
    ('NotSpecified', 'Не важно'),
    ('mahachkala', 'Махачкала'),
    ('moskva', 'Москва'),

)

MAKHACHKALA_DISTRICTS = (
    ('NotSpecified', 'Не важно'),
    ('р-н Кировский', 'р-н Кировский'),
    ('р-н Советский', 'р-н Советский'),
    ('р-н Ленинский', 'р-н Ленинский'),
)


class FilterForm(forms.Form):
    region = forms.ChoiceField(choices=CITIES, required=False, label='Город')
    building_type = forms.ChoiceField(choices=BUILDING_TYPE, required=False, label='Тип здания')
    rooms = forms.ChoiceField(choices=ROOMS, required=False, label='Количество комнат')
    floor = forms.CharField(max_length=3, required=False, label='Этаж')
    floors_amount = forms.CharField(max_length=3, required=False, label='Этажей в здании')
    district = forms.ChoiceField(choices=MAKHACHKALA_DISTRICTS, required=False, label='Район')
