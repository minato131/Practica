from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Car, Booking, Review
from django.core.exceptions import ValidationError
import datetime


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
            'description': forms.Textarea(attrs={'rows': 4}),
            'year': forms.NumberInput(attrs={'min': 2000, 'max': datetime.datetime.now().year}),
        }


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

            if start_date < datetime.datetime.now():
                raise ValidationError('Нельзя бронировать на прошедшую дату')

        return cleaned_data


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment', 'car_rating', 'partner_rating']
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Оставьте ваш отзыв...'}),
        }