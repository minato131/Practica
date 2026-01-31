from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import (
    User, TransmissionType, CarStatus, BookingStatus, PaymentType,
    PaymentStatus, CarCategory, Car, Booking, Payment, Review
)

# Настройка кастомного пользователя в админке
class UserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'phone', 'driver_license')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
        (_('Дополнительно'), {'fields': ('is_verified',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_verified')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'is_verified')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('username',)

# Модель автомобиля
class CarAdmin(admin.ModelAdmin):
    list_display = ('brand', 'model', 'year', 'status', 'price_per_hour', 'partner', 'created_at')
    list_filter = ('status', 'category', 'transmission', 'year')
    search_fields = ('brand', 'model', 'description', 'address')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Основная информация', {
            'fields': ('brand', 'model', 'year', 'transmission', 'engine_type')
        }),
        ('Цены и условия', {
            'fields': ('price_per_hour', 'price_per_day', 'mileage_limit', 'category')
        }),
        ('Статус и локация', {
            'fields': ('status', 'address', 'latitude', 'longitude')
        }),
        ('Владелец и описание', {
            'fields': ('partner', 'description', 'image')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

# Модель бронирования
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'car', 'client', 'start_date', 'end_date', 'status', 'calculated_price')
    list_filter = ('status', 'start_date', 'end_date')
    search_fields = ('client__email', 'client__first_name', 'client__last_name', 'car__brand', 'car__model')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Основная информация', {
            'fields': ('client', 'car', 'status')
        }),
        ('Даты и стоимость', {
            'fields': ('start_date', 'end_date', 'calculated_price', 'final_price')
        }),
        ('Пробег', {
            'fields': ('start_mileage', 'end_mileage')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

# Модель платежа
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'booking', 'amount', 'payment_type', 'status', 'payment_date')
    list_filter = ('status', 'payment_type', 'payment_date')
    search_fields = ('booking__id', 'transaction_id')
    readonly_fields = ('payment_date',)

# Модель отзыва
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('booking', 'rating', 'car_rating', 'partner_rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('booking__id', 'comment')
    readonly_fields = ('created_at',)

# Регистрация моделей в админке
admin.site.register(User, UserAdmin)
admin.site.register(TransmissionType)
admin.site.register(CarStatus)
admin.site.register(BookingStatus)
admin.site.register(PaymentType)
admin.site.register(PaymentStatus)
admin.site.register(CarCategory)
admin.site.register(Car, CarAdmin)
admin.site.register(Booking, BookingAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(Review, ReviewAdmin)

# Настройка заголовков админки
admin.site.site_header = 'Администрирование Каршеринга'
admin.site.site_title = 'Каршеринг'
admin.site.index_title = 'Панель управления'