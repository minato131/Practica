from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Car, Booking, Review, SupportChat, SupportMessage,  PartnerPayout
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
    class Meta:
        model = Booking
        fields = ['start_date', 'end_date', 'car']
        widgets = {
            'start_date': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control',
                'min': timezone.now().strftime('%Y-%m-%dT%H:%M')
            }),
            'end_date': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control',
                'min': timezone.now().strftime('%Y-%m-%dT%H:%M')
            }),
            'car': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['car'].required = False

    def clean_start_date(self):
        start_date = self.cleaned_data.get('start_date')
        if start_date:
            # Делаем дату timezone-aware если она naive
            if timezone.is_naive(start_date):
                start_date = timezone.make_aware(start_date)

            # Проверяем что дата не в прошлом
            if start_date < timezone.now():
                raise forms.ValidationError(
                    "Дата начала не может быть в прошлом. Вы выбрали: %s" % start_date.strftime('%d.%m.%Y %H:%M'))
        return start_date

    def clean_end_date(self):
        end_date = self.cleaned_data.get('end_date')
        start_date = self.cleaned_data.get('start_date')

        if end_date:
            # Делаем дату timezone-aware если она naive
            if timezone.is_naive(end_date):
                end_date = timezone.make_aware(end_date)

            # Проверяем что дата окончания не в прошлом
            if end_date < timezone.now():
                raise forms.ValidationError("Дата окончания не может быть в прошлом")

            # Проверяем что дата окончания позже даты начала
            if start_date and end_date <= start_date:
                raise forms.ValidationError("Дата окончания должна быть позже даты начала")

            # Проверяем минимальную продолжительность (минимум 1 час)
            if start_date and (end_date - start_date).total_seconds() < 3600:
                raise forms.ValidationError("Минимальная продолжительность бронирования - 1 час")

        return end_date

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        car = cleaned_data.get('car')

        if not start_date or not end_date:
            return cleaned_data

        # Проверяем пересечения с другими бронированиями
        if car:
            overlapping = Booking.objects.filter(
                car=car,
                start_date__lt=end_date,
                end_date__gt=start_date,
                status__name__in=['подтверждено', 'активно']
            ).exists()

            if overlapping:
                raise forms.ValidationError("Автомобиль уже забронирован на выбранные даты")

        return cleaned_data

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'car_rating', 'partner_rating', 'comment', 'advantages', 'disadvantages']
        widgets = {
            'rating': forms.RadioSelect(attrs={'class': 'star-rating', 'data-type': 'main'}),
            'car_rating': forms.RadioSelect(attrs={'class': 'star-rating', 'data-type': 'car'}),
            'partner_rating': forms.RadioSelect(attrs={'class': 'star-rating', 'data-type': 'partner'}),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Поделитесь впечатлениями о поездке...'
            }),
            'advantages': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Что вам особенно понравилось?'
            }),
            'disadvantages': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Что можно было бы улучшить?'
            }),
        }
        labels = {
            'rating': 'Общая оценка',
            'car_rating': 'Оценка автомобиля',
            'partner_rating': 'Оценка партнера',
            'comment': 'Ваш отзыв',
            'advantages': 'Достоинства',
            'disadvantages': 'Недостатки',
        }
        help_texts = {
            'rating': 'Насколько вы довольны поездкой?',
            'car_rating': 'Как вам состояние автомобиля?',
            'partner_rating': 'Как вам взаимодействие с владельцем?',
        }

class SupportChatForm(forms.ModelForm):
    class Meta:
        model = SupportChat
        fields = ['subject']
        widgets = {
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Кратко опишите ваш вопрос'
            })
        }

class SupportMessageForm(forms.ModelForm):
    class Meta:
        model = SupportMessage
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Введите ваше сообщение...'
            })
        }

class PartnerCarForm(forms.ModelForm):
    """Форма для добавления/редактирования автомобиля партнером"""
    class Meta:
        model = Car
        fields = [
            'brand', 'model', 'year', 'transmission', 'engine_type',
            'price_per_hour', 'price_per_day', 'mileage_limit',
            'description', 'address', 'category', 'image'
        ]
        widgets = {
            'brand': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Например: Toyota',
                'autocomplete': 'off'
            }),
            'model': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Например: Camry',
                'autocomplete': 'off'
            }),
            'year': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 2000,
                'max': 2026,
                'placeholder': '2023'
            }),
            'transmission': forms.Select(attrs={
                'class': 'form-select'
            }),
            'engine_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'price_per_hour': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'step': '0.01',
                'placeholder': '500'
            }),
            'price_per_day': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'step': '0.01',
                'placeholder': '3000'
            }),
            'mileage_limit': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'value': 200,
                'placeholder': '200'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Опишите ваш автомобиль: состояние, особенности, комплектацию...'
            }),
            'address': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'ул. Ленина, 10, Москва',
                'autocomplete': 'off'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
        }
        labels = {
            'brand': 'Марка',
            'model': 'Модель',
            'year': 'Год выпуска',
            'transmission': 'Коробка передач',
            'engine_type': 'Тип двигателя',
            'price_per_hour': 'Цена за час (₽)',
            'price_per_day': 'Цена за сутки (₽)',
            'mileage_limit': 'Лимит пробега в день (км)',
            'description': 'Описание',
            'address': 'Адрес',
            'category': 'Категория',
            'image': 'Фото автомобиля',
        }
        help_texts = {
            'mileage_limit': 'Максимальный пробег в день без доплаты',
            'address': 'Адрес, где находится автомобиль',
            'image': 'Загрузите основное фото автомобиля',
        }

class PartnerProfileForm(forms.ModelForm):
    """Форма для редактирования профиля партнера"""
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'phone',
            'company_name', 'inn', 'bank_details'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+7 (999) 123-45-67'}),
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
            'inn': forms.TextInput(attrs={'class': 'form-control'}),
            'bank_details': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class PayoutRequestForm(forms.ModelForm):
    """Форма для запроса выплаты"""
    class Meta:
        model = PartnerPayout
        fields = ['amount', 'payment_method', 'notes']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'min': 100, 'step': '100'}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Дополнительная информация'}),
        }
        labels = {
            'amount': 'Сумма выплаты (₽)',
            'payment_method': 'Способ получения',
            'notes': 'Комментарий',
        }