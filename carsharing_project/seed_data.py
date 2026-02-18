#!/usr/bin/env python
"""
Скрипт для заполнения базы данных тестовыми данными.
Запуск: python seed_data.py
"""

import os
import sys
import django
import random
from datetime import timedelta
from django.utils import timezone
from decimal import Decimal

# Настройка Django окружения
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'carsharing_project.settings')
django.setup()

from cars.models import (
    User, Car, CarImage, Booking, CarStatus, BookingStatus,
    PaymentType, PaymentStatus, TransmissionType, CarCategory, Review, Payment
)

# Словарь с тестовыми данными
MOCK_CARS = [
    {
        'brand': 'Toyota',
        'model': 'Camry',
        'year': 2022,
        'price_per_hour': 500,
        'price_per_day': 3000,
        'description': 'Комфортный седан для деловых поездок. Кондиционер, круиз-контроль, подогрев сидений.',
        'transmission': 'Автомат',
        'engine_type': 'Бензин'
    },
    {
        'brand': 'BMW',
        'model': 'X5',
        'year': 2023,
        'price_per_hour': 1200,
        'price_per_day': 7000,
        'description': 'Премиальный внедорожник. Полный привод, кожаный салон, панорамная крыша.',
        'transmission': 'Автомат',
        'engine_type': 'Дизель'
    },
    {
        'brand': 'Kia',
        'model': 'Rio',
        'year': 2021,
        'price_per_hour': 400,
        'price_per_day': 2000,
        'description': 'Экономичный и надежный автомобиль для города. Отлично подходит для начинающих водителей.',
        'transmission': 'Механика',
        'engine_type': 'Бензин'
    },
    {
        'brand': 'Hyundai',
        'model': 'Solaris',
        'year': 2022,
        'price_per_hour': 450,
        'price_per_day': 2200,
        'description': 'Популярный автомобиль с хорошей управляемостью и экономичным расходом топлива.',
        'transmission': 'Автомат',
        'engine_type': 'Бензин'
    },
    {
        'brand': 'Mercedes-Benz',
        'model': 'E-Class',
        'year': 2023,
        'price_per_hour': 1500,
        'price_per_day': 8500,
        'description': 'Бизнес-класс с максимальным комфортом и передовыми технологиями безопасности.',
        'transmission': 'Автомат',
        'engine_type': 'Дизель'
    },
    {
        'brand': 'Volkswagen',
        'model': 'Polo',
        'year': 2021,
        'price_per_hour': 380,
        'price_per_day': 1900,
        'description': 'Надежный немецкий автомобиль. Просторный салон, вместительный багажник.',
        'transmission': 'Механика',
        'engine_type': 'Бензин'
    },
    {
        'brand': 'Skoda',
        'model': 'Octavia',
        'year': 2022,
        'price_per_hour': 550,
        'price_per_day': 2800,
        'description': 'Практичный лифтбек с большим багажником. Отличное соотношение цены и качества.',
        'transmission': 'Автомат',
        'engine_type': 'Бензин'
    },
    {
        'brand': 'Renault',
        'model': 'Logan',
        'year': 2020,
        'price_per_hour': 350,
        'price_per_day': 1700,
        'description': 'Простой и надежный автомобиль. Низкая стоимость обслуживания.',
        'transmission': 'Механика',
        'engine_type': 'Бензин'
    },
    {
        'brand': 'Audi',
        'model': 'Q7',
        'year': 2023,
        'price_per_hour': 1800,
        'price_per_day': 10000,
        'description': 'Роскошный внедорожник с мощным двигателем и богатым оснащением.',
        'transmission': 'Автомат',
        'engine_type': 'Дизель'
    },
    {
        'brand': 'Ford',
        'model': 'Focus',
        'year': 2021,
        'price_per_hour': 420,
        'price_per_day': 2100,
        'description': 'Динамичный хэтчбек с отличной управляемостью и современным дизайном.',
        'transmission': 'Автомат',
        'engine_type': 'Бензин'
    }
]

# Адреса для автомобилей
ADDRESSES = [
    "ул. Ленина, 10, Москва",
    "пр. Мира, 25, Москва",
    "ул. Тверская, 15, Москва",
    "Кутузовский пр., 30, Москва",
    "ул. Новый Арбат, 8, Москва",
    "Ленинградский пр., 40, Москва",
    "ул. Мясницкая, 20, Москва",
    "пр. Вернадского, 50, Москва",
    "ул. Профсоюзная, 100, Москва",
    "Рублевское шоссе, 15, Москва",
]


def create_partner():
    """Создает тестового партнера (обязательно для Car)"""
    partner, created = User.objects.get_or_create(
        username='partner',
        defaults={
            'email': 'partner@carsharing.ru',
            'first_name': 'Партнер',
            'last_name': 'Компания',
            'is_staff': True,
            'is_verified': True
        }
    )
    if created:
        partner.set_password('partner123')
        partner.save()
        print("✅ Партнер создан (partner/partner123)")
    else:
        print("⏩ Партнер уже существует")
    return partner


def create_superuser():
    """Создает суперпользователя"""
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123',
            first_name='Admin',
            last_name='Admin'
        )
        print("✅ Суперпользователь создан (admin/admin123)")
    else:
        print("⏩ Суперпользователь уже существует")


def create_test_users():
    """Создает тестовых пользователей"""
    users_data = [
        {'username': 'ivan', 'email': 'ivan@mail.ru', 'first_name': 'Иван', 'last_name': 'Петров',
         'phone': '+7(999)123-45-67', 'driver_license': '77AA123456'},
        {'username': 'maria', 'email': 'maria@mail.ru', 'first_name': 'Мария', 'last_name': 'Иванова',
         'phone': '+7(999)234-56-78', 'driver_license': '77BB234567'},
        {'username': 'petr', 'email': 'petr@mail.ru', 'first_name': 'Петр', 'last_name': 'Сидоров',
         'phone': '+7(999)345-67-89', 'driver_license': '77CC345678'},
        {'username': 'elena', 'email': 'elena@mail.ru', 'first_name': 'Елена', 'last_name': 'Козлова',
         'phone': '+7(999)456-78-90', 'driver_license': '77DD456789'},
        {'username': 'alex', 'email': 'alex@mail.ru', 'first_name': 'Алексей', 'last_name': 'Смирнов',
         'phone': '+7(999)567-89-01', 'driver_license': '77EE567890'},
    ]

    for data in users_data:
        if not User.objects.filter(username=data['username']).exists():
            User.objects.create_user(
                **data,
                password='test123',
                is_verified=True
            )
            print(f"✅ Пользователь {data['username']} создан")
        else:
            print(f"⏩ Пользователь {data['username']} уже существует")


def create_dictionaries():
    """Создает справочники"""
    # Статусы автомобилей
    car_statuses = ['доступен', 'забронирован', 'на обслуживании']
    for status in car_statuses:
        CarStatus.objects.get_or_create(name=status)

    # Статусы бронирований
    booking_statuses = ['новое', 'подтверждено', 'активно', 'завершено', 'отменено']
    for status in booking_statuses:
        BookingStatus.objects.get_or_create(name=status)

    # Типы платежей
    payment_types = ['предоплата', 'полная оплата', 'штраф', 'возврат']
    for p_type in payment_types:
        PaymentType.objects.get_or_create(name=p_type)

    # Статусы платежей
    payment_statuses = ['ожидает', 'оплачен', 'возвращен', 'просрочен']
    for status in payment_statuses:
        PaymentStatus.objects.get_or_create(name=status)

    # Типы КПП
    transmissions = ['Механика', 'Автомат', 'Робот', 'Вариатор']
    for trans in transmissions:
        TransmissionType.objects.get_or_create(name=trans)

    # Категории автомобилей
    categories = ['Эконом', 'Комфорт', 'Бизнес', 'Премиум', 'Внедорожник']
    for cat in categories:
        CarCategory.objects.get_or_create(name=cat)

    print("✅ Справочники созданы")


def create_cars(partner):
    """Создает автомобили (без изображений)"""
    cars_created = 0

    for car_data in MOCK_CARS:
        # Получаем или создаем КПП
        transmission, _ = TransmissionType.objects.get_or_create(name=car_data['transmission'])

        # Получаем категорию (определяем по цене)
        price = car_data['price_per_hour']
        if price < 400:
            category = CarCategory.objects.get(name='Эконом')
        elif price < 600:
            category = CarCategory.objects.get(name='Комфорт')
        elif price < 1000:
            category = CarCategory.objects.get(name='Бизнес')
        else:
            category = CarCategory.objects.get(name='Премиум')

        # Статус (доступен)
        status = CarStatus.objects.get(name='доступен')

        # Случайный адрес
        address = random.choice(ADDRESSES)

        # Случайный пробег
        mileage_limit = random.choice([200, 250, 300])

        # Проверяем, есть ли уже такой автомобиль
        existing_car = Car.objects.filter(
            brand=car_data['brand'],
            model=car_data['model'],
            year=car_data['year']
        ).first()

        if existing_car:
            print(f"  ⏩ Автомобиль уже существует: {car_data['brand']} {car_data['model']}")
        else:
            # Создаем новый автомобиль с ОБЯЗАТЕЛЬНЫМ partner
            Car.objects.create(
                brand=car_data['brand'],
                model=car_data['model'],
                year=car_data['year'],
                transmission=transmission,
                engine_type=car_data['engine_type'],
                price_per_hour=car_data['price_per_hour'],
                price_per_day=car_data['price_per_day'],
                mileage_limit=mileage_limit,
                description=car_data['description'],
                address=address,
                status=status,
                category=category,
                partner=partner,
            )
            cars_created += 1
            print(f"  ✅ Создан автомобиль: {car_data['brand']} {car_data['model']}")

    print(f"✅ Всего создано {cars_created} новых автомобилей")


def create_bookings():
    """Создает тестовые бронирования"""
    users = User.objects.filter(is_superuser=False, is_staff=False)
    cars = Car.objects.all()
    booking_statuses = BookingStatus.objects.all()
    payment_types = PaymentType.objects.all()
    payment_statuses = PaymentStatus.objects.all()

    bookings_created = 0

    for user in users:
        for _ in range(random.randint(1, 2)):  # У каждого пользователя 1-2 бронирования
            if not cars:
                continue
            car = random.choice(cars)
            status = random.choice(booking_statuses)

            # Генерируем даты
            start_date = timezone.now() + timedelta(days=random.randint(-5, 10))
            hours = random.randint(2, 72)
            end_date = start_date + timedelta(hours=hours)

            # Проверяем пересечения
            if not Booking.objects.filter(
                    car=car,
                    start_date__lt=end_date,
                    end_date__gt=start_date
            ).exists():

                booking = Booking.objects.create(
                    client=user,
                    car=car,
                    start_date=start_date,
                    end_date=end_date,
                    status=status,
                    calculated_price=car.price_per_hour * hours,
                    created_at=timezone.now() - timedelta(days=random.randint(1, 10))
                )

                # Создаем платеж
                payment_type = random.choice(payment_types)
                payment_status = random.choice(payment_statuses)

                if status.name in ['подтверждено', 'активно', 'завершено']:
                    payment_amount = booking.calculated_price * Decimal('0.3')
                else:
                    payment_amount = Decimal('0')

                Payment.objects.create(
                    booking=booking,
                    amount=payment_amount,
                    payment_type=payment_type,
                    status=payment_status,
                    payment_date=timezone.now() if payment_status.name == 'оплачен' else None
                )

                bookings_created += 1
                print(f"  ✅ Бронирование #{booking.id} для {user.username}")

    print(f"✅ Создано {bookings_created} бронирований")


def create_reviews():
    """Создает отзывы"""
    bookings = Booking.objects.filter(status__name='завершено')[:10]
    reviews_created = 0

    for booking in bookings:
        if not hasattr(booking, 'review'):
            Review.objects.create(
                booking=booking,
                rating=random.randint(3, 5),
                car_rating=random.randint(3, 5),
                partner_rating=random.randint(3, 5),
                comment=random.choice([
                    "Отличный автомобиль, всё понравилось!",
                    "Хорошая машина, но есть мелкие недочеты",
                    "Всё супер, обязательно возьму еще",
                    "Машина в хорошем состоянии, спасибо",
                    "Немного задержали подачу, но в целом ок"
                ]),
                created_at=timezone.now() - timedelta(days=random.randint(1, 30))
            )
            reviews_created += 1
            print(f"  ✅ Отзыв для бронирования #{booking.id}")

    print(f"✅ Создано {reviews_created} отзывов")


def clear_database():
    """Очищает базу данных"""
    print("\n🧹 Очистка базы данных...")

    # Удаляем в правильном порядке (с учетом внешних ключей)
    Review.objects.all().delete()
    Payment.objects.all().delete()
    Booking.objects.all().delete()
    CarImage.objects.all().delete()
    Car.objects.all().delete()

    # Не удаляем пользователей и справочники
    # User.objects.filter(is_superuser=False).delete()

    print("✅ База данных очищена")


def main():
    """Главная функция"""
    print("\n" + "=" * 50)
    print("🚗 ЗАПОЛНЕНИЕ БАЗЫ ДАННЫХ ТЕСТОВЫМИ ДАННЫМИ")
    print("=" * 50)

    # Спрашиваем, очищать ли базу
    response = input("\nОчистить базу перед заполнением? (y/n): ").lower()
    if response == 'y':
        clear_database()

    print("\n📦 Создание справочников...")
    create_dictionaries()

    print("\n👤 Создание пользователей...")
    create_superuser()
    create_test_users()

    print("\n🏢 Создание партнера...")
    partner = create_partner()

    print("\n🚘 Создание автомобилей...")
    create_cars(partner)

    print("\n📅 Создание бронирований...")
    create_bookings()

    print("\n⭐ Создание отзывов...")
    create_reviews()

    print("\n" + "=" * 50)
    print("✅ ЗАПОЛНЕНИЕ ЗАВЕРШЕНО!")
    print("=" * 50)

    # Статистика
    print(f"\n📊 Статистика:")
    print(f"   Пользователей: {User.objects.count()}")
    print(f"   Партнеров: {User.objects.filter(username='partner').count()}")
    print(f"   Автомобилей: {Car.objects.count()}")
    print(f"   Изображений: {CarImage.objects.count()}")
    print(f"   Бронирований: {Booking.objects.count()}")
    print(f"   Платежей: {Payment.objects.count()}")
    print(f"   Отзывов: {Review.objects.count()}")


if __name__ == '__main__':
    main()