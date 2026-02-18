from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import os

class CustomUserManager(BaseUserManager):
    def create_user(self, email, username, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, username, password, **extra_fields)


class User(AbstractUser):
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    driver_license = models.CharField(max_length=50, blank=True)
    is_verified = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    objects = CustomUserManager()

    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"

    def get_role_display(self):
        if self.is_superuser:
            return 'Администратор'
        elif self.is_staff and not self.is_superuser:
            return 'Менеджер'
        else:
            return 'Клиент'

    @property
    def is_manager(self):
        """Проверяет, является ли пользователь менеджером"""
        return self.is_staff and not self.is_superuser

    @property
    def is_client(self):
        """Проверяет, является ли пользователь клиентом"""
        return not self.is_staff and not self.is_superuser

class TransmissionType(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class CarStatus(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class CarCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

def car_image_upload_path(instance, filename):
    """Генерирует путь для загрузки изображений"""
    # Получаем расширение файла
    ext = filename.split('.')[-1]
    # Генерируем новое имя файла
    filename = f"{instance.car.id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.{ext}"
    # Возвращаем путь: cars/<car_id>/images/<filename>
    return os.path.join('cars', str(instance.car.id), 'images', filename)

class CarImage(models.Model):
    """Модель для изображений автомобиля"""
    car = models.ForeignKey('Car', on_delete=models.CASCADE, related_name='images', verbose_name="Автомобиль")
    image = models.ImageField(upload_to=car_image_upload_path, verbose_name="Изображение")
    is_main = models.BooleanField(default=False, verbose_name="Главное изображение")
    caption = models.CharField(max_length=200, blank=True, verbose_name="Подпись")
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок сортировки")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата добавления")

    class Meta:
        verbose_name = "Изображение автомобиля"
        verbose_name_plural = "Изображения автомобилей"
        ordering = ['order', 'created_at']

    def __str__(self):
        return f"Изображение для {self.car.brand} {self.car.model}"

    def save(self, *args, **kwargs):
        # Если это главное изображение, сбрасываем главные у других изображений этого автомобиля
        if self.is_main:
            CarImage.objects.filter(car=self.car, is_main=True).update(is_main=False)
        super().save(*args, **kwargs)

class Car(models.Model):
    brand = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    year = models.IntegerField()
    transmission = models.ForeignKey(TransmissionType, on_delete=models.PROTECT)
    engine_type = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)
    price_per_hour = models.DecimalField(max_digits=10, decimal_places=2)
    price_per_day = models.DecimalField(max_digits=10, decimal_places=2)
    mileage_limit = models.IntegerField(null=True, blank=True)
    status = models.ForeignKey(CarStatus, on_delete=models.PROTECT, default=1)
    latitude = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    longitude = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    address = models.CharField(max_length=255, blank=True)
    partner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cars')
    category = models.ForeignKey(CarCategory, on_delete=models.SET_NULL, null=True, blank=True)
    image = models.ImageField(upload_to='car_images/', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    role = models.CharField(max_length=20, default='client', blank=True)

    def __str__(self):
        return f"{self.brand} {self.model} ({self.year})"

    @property
    def is_available(self):
        return self.status.name == 'доступен'

    def get_main_image(self):
        """Возвращает URL главного изображения"""
        main_image = self.images.filter(is_main=True).first()
        if main_image:
            return main_image.image.url
        first_image = self.images.first()
        if first_image:
            return first_image.image.url
        return '/static/images/no-image.png'

    def get_all_images(self):
        """Возвращает все изображения автомобиля"""
        return self.images.all().order_by('order', 'created_at')

    def get_images_count(self):
        """Возвращает количество изображений"""
        return self.images.count()

    def get_average_rating(self):
        """Средняя оценка автомобиля"""
        reviews = self.reviews.filter(is_published=True)
        if reviews:
            return round(sum(r.rating for r in reviews) / reviews.count(), 1)
        return 0

    def get_reviews_count(self):
        """Количество отзывов"""
        return self.reviews.filter(is_published=True).count()

    def get_reviews(self):
        """Все опубликованные отзывы"""
        return self.reviews.filter(is_published=True).order_by('-created_at')

    # Добавляем связь с отзывами
    @property
    def reviews(self):
        return Review.objects.filter(booking__car=self)

    ROLE_CHOICES = (
        ('client', 'Клиент'),
        ('partner', 'Партнер'),
        ('admin', 'Администратор'),
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='client',
        verbose_name='Роль'
    )


class BookingStatus(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Booking(models.Model):
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='bookings')
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    calculated_price = models.DecimalField(max_digits=10, decimal_places=2)
    final_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.ForeignKey(BookingStatus, on_delete=models.PROTECT, default=1)
    start_mileage = models.IntegerField(null=True, blank=True)
    end_mileage = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Бронирование #{self.id} - {self.car} от {self.client}"

    def save(self, *args, **kwargs):
        if not self.final_price:
            self.final_price = self.calculated_price
        super().save(*args, **kwargs)


class PaymentType(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class PaymentStatus(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Payment(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_type = models.ForeignKey(PaymentType, on_delete=models.PROTECT)
    status = models.ForeignKey(PaymentStatus, on_delete=models.PROTECT, default=1)
    transaction_id = models.CharField(max_length=255, blank=True)
    payment_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Платеж #{self.id} - {self.amount} руб."


class Review(models.Model):
    """Модель отзыва"""
    booking = models.OneToOneField(
        'Booking',
        on_delete=models.CASCADE,
        related_name='review',
        verbose_name='Бронирование'
    )
    rating = models.IntegerField(
        choices=[(i, i) for i in range(1, 6)],
        verbose_name='Общая оценка'
    )
    car_rating = models.IntegerField(
        choices=[(i, i) for i in range(1, 6)],
        verbose_name='Оценка автомобиля'
    )
    partner_rating = models.IntegerField(
        choices=[(i, i) for i in range(1, 6)],
        verbose_name='Оценка партнера',
        null=True,
        blank=True
    )
    comment = models.TextField(verbose_name='Комментарий')
    advantages = models.TextField(
        verbose_name='Достоинства',
        blank=True
    )
    disadvantages = models.TextField(
        verbose_name='Недостатки',
        blank=True
    )
    is_published = models.BooleanField(
        default=True,
        verbose_name='Опубликован'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        ordering = ['-created_at']

    def __str__(self):
        return f'Отзыв #{self.id} от {self.booking.client.username} на {self.booking.car}'

    @property
    def car(self):
        return self.booking.car

    @property
    def user(self):
        return self.booking.client

class SupportChat(models.Model):
    """Модель чата поддержки"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='support_chats',
        verbose_name='Пользователь'
    )
    admin = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='admin_chats',
        verbose_name='Администратор'
    )
    subject = models.CharField(
        max_length=200,
        verbose_name='Тема'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активен'
    )
    is_closed = models.BooleanField(
        default=False,
        verbose_name='Закрыт'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Создан'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Обновлен'
    )
    closed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Закрыт'
    )

    class Meta:
        verbose_name = 'Чат поддержки'
        verbose_name_plural = 'Чаты поддержки'
        ordering = ['-updated_at']

    def __str__(self):
        return f'Чат #{self.id} - {self.user.username} - {self.subject[:30]}'

    def get_last_message(self):
        return self.messages.order_by('-created_at').first()

    def get_unread_count(self):
        """Количество непрочитанных сообщений для текущего пользователя"""
        # Если нужно фильтровать по пользователю, передавайте его как параметр
        return self.messages.filter(is_read=False).count()

class SupportMessage(models.Model):
    """Модель сообщения в чате"""
    chat = models.ForeignKey(
        SupportChat,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name='Чат'
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_messages',
        verbose_name='Отправитель'
    )
    message = models.TextField(
        verbose_name='Сообщение'
    )
    is_read = models.BooleanField(
        default=False,
        verbose_name='Прочитано'
    )
    is_system = models.BooleanField(
        default=False,
        verbose_name='Системное'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Отправлено'
    )

    class Meta:
        verbose_name = 'Сообщение'
        verbose_name_plural = 'Сообщения'
        ordering = ['created_at']

    def __str__(self):
        return f'Сообщение от {self.sender.username} в чате #{self.chat.id}'