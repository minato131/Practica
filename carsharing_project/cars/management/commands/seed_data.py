from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from cars.models import (
    TransmissionType, CarStatus, BookingStatus,
    PaymentType, PaymentStatus, CarCategory, Car
)
from datetime import datetime, timedelta

User = get_user_model()


class Command(BaseCommand):
    help = 'Загружает начальные данные для тестирования'

    def handle(self, *args, **kwargs):
        self.stdout.write('Начинаем загрузку данных...')

        # Создаем суперпользователя если его нет
        if not User.objects.filter(email='admin@carsharing.ru').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@carsharing.ru',
                password='admin123',
                first_name='Администратор',
                last_name='Системы',
                phone='+7 (999) 123-45-67',
                driver_license='77AA123456'
            )
            self.stdout.write(self.style.SUCCESS('Создан суперпользователь: admin@carsharing.ru / admin123'))

        if not User.objects.filter(email='manager@carsharing.ru').exists():
            User.objects.create_user(
                username='manager',
                email='manager@carsharing.ru',
                password='manager123',
                first_name='Менеджер',
                last_name='Каршеринга',
                phone='+7 (999) 888-77-66',
                driver_license='77CC987654',
                is_staff=True,  # Важно: is_staff = True, is_superuser = False
                is_superuser=False
            )
            self.stdout.write(self.style.SUCCESS('Создан менеджер: manager@carsharing.ru / manager123'))

        # Создаем тестового пользователя
        if not User.objects.filter(email='user@test.ru').exists():
            User.objects.create_user(
                username='testuser',
                email='user@test.ru',
                password='test123',
                first_name='Иван',
                last_name='Петров',
                phone='+7 (999) 765-43-21',
                driver_license='77BB654321'
            )
            self.stdout.write(self.style.SUCCESS('Создан тестовый пользователь: user@test.ru / test123'))

        # Создаем справочные данные если их нет
        transmission_types = ['автомат', 'механика']
        for name in transmission_types:
            TransmissionType.objects.get_or_create(name=name)

        car_statuses = ['доступен', 'забронирован', 'на обслуживании', 'недоступен']
        for name in car_statuses:
            CarStatus.objects.get_or_create(name=name)

        booking_statuses = ['подтверждено', 'активно', 'завершено', 'отменено']
        for name in booking_statuses:
            BookingStatus.objects.get_or_create(name=name)

        payment_types = ['предоплата', 'полная оплата', 'штраф', 'возврат']
        for name in payment_types:
            PaymentType.objects.get_or_create(name=name)

        payment_statuses = ['ожидает', 'успешен', 'неудачен', 'возвращен']
        for name in payment_statuses:
            PaymentStatus.objects.get_or_create(name=name)

        # Создаем категории автомобилей
        categories = [
            ('Эконом', 'Бюджетные автомобили для городских поездок'),
            ('Комфорт', 'Автомобили среднего класса с повышенным комфортом'),
            ('Бизнес', 'Премиум автомобили для деловых поездок'),
            ('Внедорожник', 'Автомобили повышенной проходимости'),
            ('Премиум', 'Люкс автомобили')
        ]

        for name, description in categories:
            CarCategory.objects.get_or_create(
                name=name,
                defaults={'description': description}
            )

        # Создаем тестовые автомобили
        if not Car.objects.exists():
            admin_user = User.objects.get(email='admin@carsharing.ru')
            available_status = CarStatus.objects.get(name='доступен')
            transmission_auto = TransmissionType.objects.get(name='автомат')
            transmission_mech = TransmissionType.objects.get(name='механика')

            cars_data = [
                {
                    'brand': 'Toyota',
                    'model': 'Camry',
                    'year': 2022,
                    'transmission': transmission_auto,
                    'engine_type': 'Бензин 2.5L',
                    'description': 'Комфортабельный седан бизнес-класса. Кондиционер, кожаный салон, навигация.',
                    'price_per_hour': 500,
                    'price_per_day': 4500,
                    'mileage_limit': 300,
                    'category': CarCategory.objects.get(name='Бизнес'),
                    'address': 'Москва, ул. Тверская, д. 10',
                },
                {
                    'brand': 'Kia',
                    'model': 'Rio',
                    'year': 2021,
                    'transmission': transmission_mech,
                    'engine_type': 'Бензин 1.6L',
                    'description': 'Экономичный городской автомобиль. Идеально для ежедневных поездок.',
                    'price_per_hour': 250,
                    'price_per_day': 2000,
                    'mileage_limit': 250,
                    'category': CarCategory.objects.get(name='Эконом'),
                    'address': 'Москва, Ленинский проспект, д. 25',
                },
                {
                    'brand': 'BMW',
                    'model': 'X5',
                    'year': 2023,
                    'transmission': transmission_auto,
                    'engine_type': 'Дизель 3.0L',
                    'description': 'Премиальный внедорожник. Полный привод, панорамная крыша, premium-аудиосистема.',
                    'price_per_hour': 800,
                    'price_per_day': 6500,
                    'mileage_limit': 350,
                    'category': CarCategory.objects.get(name='Премиум'),
                    'address': 'Москва, Кутузовский проспект, д. 32',
                },
                {
                    'brand': 'Hyundai',
                    'model': 'Solaris',
                    'year': 2020,
                    'transmission': transmission_auto,
                    'engine_type': 'Бензин 1.6L',
                    'description': 'Надежный и экономичный автомобиль. Автоматическая коробка передач, кондиционер.',
                    'price_per_hour': 300,
                    'price_per_day': 2500,
                    'mileage_limit': 300,
                    'category': CarCategory.objects.get(name='Комфорт'),
                    'address': 'Москва, проспект Мира, д. 15',
                },
                {
                    'brand': 'Lada',
                    'model': 'Vesta',
                    'year': 2021,
                    'transmission': transmission_mech,
                    'engine_type': 'Бензин 1.8L',
                    'description': 'Популярный отечественный автомобиль. Прост в обслуживании, экономичен.',
                    'price_per_hour': 200,
                    'price_per_day': 1500,
                    'mileage_limit': 200,
                    'category': CarCategory.objects.get(name='Эконом'),
                    'address': 'Москва, ул. Арбат, д. 5',
                },
                {
                    'brand': 'Mercedes',
                    'model': 'E-Class',
                    'year': 2023,
                    'transmission': transmission_auto,
                    'engine_type': 'Бензин 2.0L',
                    'description': 'Представительский класс. Максимальный комфорт, передовые технологии.',
                    'price_per_hour': 900,
                    'price_per_day': 7500,
                    'mileage_limit': 400,
                    'category': CarCategory.objects.get(name='Премиум'),
                    'address': 'Москва, ул. Новый Арбат, д. 21',
                },
            ]

            for car_data in cars_data:
                Car.objects.create(
                    partner=admin_user,
                    status=available_status,
                    **car_data
                )

            self.stdout.write(self.style.SUCCESS(f'Создано {len(cars_data)} тестовых автомобилей'))

        self.stdout.write(self.style.SUCCESS('Данные успешно загружены!'))
        self.stdout.write('=' * 50)
        self.stdout.write('Доступные учетные записи:')
        self.stdout.write('1. Администратор: admin@carsharing.ru / admin123')
        self.stdout.write('2. Пользователь: user@test.ru / test123')
        self.stdout.write('=' * 50)