from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import User, Car, CarImage, Booking, CarStatus, BookingStatus, Payment, PaymentType, PaymentStatus, \
    TransmissionType, CarCategory, Review


class CarImageInline(admin.TabularInline):
    """Инлайн для загрузки нескольких изображений автомобиля"""
    model = CarImage
    extra = 3
    fields = ['image', 'is_main', 'caption', 'order', 'image_preview']
    readonly_fields = ['image_preview']

    def image_preview(self, obj):
        if obj and obj.image:
            return format_html('<img src="{}" style="max-height: 100px; max-width: 100px; border-radius: 5px;" />',
                               obj.image.url)
        return "Нет изображения"

    image_preview.short_description = "Превью"


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
    list_display = ('brand', 'model', 'year', 'status', 'price_per_hour', 'partner', 'main_image_preview', 'created_at')
    list_filter = ('status', 'category', 'transmission', 'year')
    search_fields = ('brand', 'model', 'description', 'address')
    readonly_fields = ('created_at', 'updated_at', 'all_images_preview')
    inlines = [CarImageInline]  # Добавляем инлайн для изображений

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
            'fields': ('partner', 'description')
        }),
        ('Изображения', {
            'fields': ('all_images_preview',),
            'classes': ('collapse',),
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def main_image_preview(self, obj):
        """Превью главного изображения в списке"""
        main_image = obj.get_main_image()
        if main_image and main_image != '/static/images/no-image.png':
            return format_html('<img src="{}" style="max-height: 50px; max-width: 50px; border-radius: 5px;" />',
                               main_image)
        return "Нет фото"

    main_image_preview.short_description = "Фото"

    def all_images_preview(self, obj):
        """Превью всех изображений на детальной странице"""
        images = obj.get_all_images()
        if images:
            html = '<div style="display: flex; flex-wrap: wrap; gap: 10px;">'
            for img in images:
                html += f'<div style="text-align: center;">'
                html += f'<img src="{img.image.url}" style="max-height: 100px; max-width: 100px; border-radius: 5px;" />'
                if img.is_main:
                    html += '<br><span class="badge bg-success">Главное</span>'
                if img.caption:
                    html += f'<br><small>{img.caption}</small>'
                html += '</div>'
            html += '</div>'
            return format_html(html)
        return "Нет изображений"

    all_images_preview.short_description = "Все изображения"


# Модель изображений автомобиля
class CarImageAdmin(admin.ModelAdmin):
    list_display = ('car', 'image_preview', 'is_main', 'order', 'created_at')
    list_filter = ('is_main', 'car__brand')
    search_fields = ('car__brand', 'car__model', 'caption')
    list_editable = ('is_main', 'order')

    def image_preview(self, obj):
        if obj and obj.image:
            return format_html('<img src="{}" style="max-height: 50px; max-width: 50px; border-radius: 5px;" />',
                               obj.image.url)
        return "Нет изображения"

    image_preview.short_description = "Превью"


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
    list_display = ('id', 'car_info', 'user_info', 'rating', 'car_rating', 'is_published', 'created_at')
    list_filter = ('rating', 'is_published', 'created_at')
    search_fields = ('booking__client__username', 'booking__client__email', 'comment')
    list_editable = ('is_published',)
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Информация о бронировании', {
            'fields': ('booking',)
        }),
        ('Оценки', {
            'fields': ('rating', 'car_rating', 'partner_rating')
        }),
        ('Текст отзыва', {
            'fields': ('comment', 'advantages', 'disadvantages')
        }),
        ('Публикация', {
            'fields': ('is_published', 'created_at', 'updated_at')
        }),
    )

    def car_info(self, obj):
        return str(obj.booking.car)

    car_info.short_description = 'Автомобиль'

    def user_info(self, obj):
        return obj.booking.client.username

    user_info.short_description = 'Пользователь'

# Регистрация моделей в админке
admin.site.register(User, UserAdmin)
admin.site.register(TransmissionType)
admin.site.register(CarStatus)
admin.site.register(BookingStatus)
admin.site.register(PaymentType)
admin.site.register(PaymentStatus)
admin.site.register(CarCategory)
admin.site.register(Car, CarAdmin)
admin.site.register(CarImage, CarImageAdmin)  # Регистрируем модель изображений
admin.site.register(Booking, BookingAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(Review, ReviewAdmin)

# Настройка заголовков админки
admin.site.site_header = 'Администрирование Каршеринга'
admin.site.site_title = 'Каршеринг'
admin.site.index_title = 'Панель управления'