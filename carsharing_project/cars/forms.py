from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Car, Booking, Review
from django.core.exceptions import ValidationError
import datetime
from django.utils import timezone

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(label='Email')
    first_name = forms.CharField(label='Имя', max_length=30)
    last_name = forms.CharField(label='Фамилия', max_length=30)
    phone = forms.CharField(label='Телефон', max_length=20, required=False)
    driver_license = forms.CharField(label='Водительское удостоверение', max_length=50, required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'phone',
                  'driver_license', 'password1', 'password2']


class CarForm(forms.ModelForm):
    class Meta:
        model = Car
        fields = ['brand', 'model', 'year', 'transmission', 'engine_type',
                  'description', 'price_per_hour', 'price_per_day', 'mileage_limit',
                  'category', 'address', 'image']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Опишите особенности автомобиля...'}),
            'year': forms.NumberInput(attrs={'min': 2000, 'max': datetime.datetime.now().year}),
            'price_per_hour': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'price_per_day': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'mileage_limit': forms.NumberInput(attrs={'min': '0', 'placeholder': 'Оставьте пустым для безлимита'}),
            'address': forms.TextInput(attrs={'placeholder': 'Например: Москва, ул. Тверская, д. 10'}),
        }
        labels = {
            'brand': 'Марка',
            'model': 'Модель',
            'year': 'Год выпуска',
            'transmission': 'Трансмиссия',
            'engine_type': 'Тип двигателя',
            'description': 'Описание',
            'price_per_hour': 'Цена в час (₽)',
            'price_per_day': 'Цена в сутки (₽)',
            'mileage_limit': 'Лимит пробега (км/сутки)',
            'category': 'Категория',
            'address': 'Адрес',
            'image': 'Фотография автомобиля',
        }

    def clean_price_per_hour(self):
        price = self.cleaned_data.get('price_per_hour')
        if price <= 0:
            raise ValidationError('Цена должна быть больше 0')
        return price

    def clean_price_per_day(self):
        price = self.cleaned_data.get('price_per_day')
        if price <= 0:
            raise ValidationError('Цена должна быть больше 0')
        return price

    def clean_year(self):
        year = self.cleaned_data.get('year')
        current_year = datetime.datetime.now().year
        if year < 2000 or year > current_year:
            raise ValidationError(f'Год должен быть между 2000 и {current_year}')
        return year


class BookingForm(forms.ModelForm):
    start_date = forms.DateTimeField(
        label='Дата начала',
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        input_formats=['%Y-%m-%dT%H:%M']
    )
    end_date = forms.DateTimeField(
        label='Дата окончания',
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        input_formats=['%Y-%m-%dT%H:%M']
    )

    class Meta:
        model = Booking
        fields = ['start_date', 'end_date']

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date:
            if start_date >= end_date:
                raise ValidationError('Дата окончания должна быть позже даты начала')

            if start_date < timezone.now():
                raise ValidationError('Нельзя бронировать на прошедшую дату')

            # Минимальная аренда - 1 час
            duration = end_date - start_date
            if duration.total_seconds() < 3600:
                raise ValidationError('Минимальное время аренды - 1 час')

        return cleaned_data


class ReviewForm(forms.ModelForm):
    rating = forms.IntegerField(
        min_value=1,
        max_value=5,
        widget=forms.HiddenInput(),
        initial=5
    )

    class Meta:
        model = Review
        fields = ['rating', 'comment', 'car_rating', 'partner_rating']
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Оставьте ваш отзыв...'}),
            'car_rating': forms.HiddenInput(),
            'partner_rating': forms.HiddenInput(),
        }
        labels = {
            'comment': 'Комментарий',
            'car_rating': 'Оценка автомобиля',
            'partner_rating': 'Оценка партнера',
        }