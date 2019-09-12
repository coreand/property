from django import forms

BUILDING_TYPE = (
    ('NotSpecified', 'Не важно'),
    ('Brick', 'Кирпичный'),
    ('Panel', 'Панельный'),
    ('Block', 'Блочный'),
    ('Monolith', 'Монолитный'),
    ('Wooden', 'Деревянный'),
)

ROOMS = (
    ('NotSpecified', 'Не важно'),
    ('Studio', 'Студия'),
    ('FreeLayout', 'Свободная планировка'),
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
    ('Makhachkala', 'Махачкала'),

)

MAKHACHKALA_DISTRICTS = (
    ('NotSpecified', 'Не важно'),
    ('Kirovskiy', 'р-н Кировский'),
    ('Sovetskiy', 'р-н Советский'),
    ('Leninskiy', 'р-н Ленинский'),
)


class FilterForm(forms.Form):
    region = forms.ChoiceField(choices=CITIES, required=False, label='Город')
    building_type = forms.ChoiceField(choices=BUILDING_TYPE, required=False, label='Тип здания')
    rooms = forms.ChoiceField(choices=ROOMS, required=False, label='Количество комнат')
    floor = forms.CharField(max_length=3, required=False, label='Этаж')
    floors_amount = forms.CharField(max_length=3, required=False, label='Этажей в здании')
    district = forms.ChoiceField(choices=MAKHACHKALA_DISTRICTS, required=False, label='Район')
