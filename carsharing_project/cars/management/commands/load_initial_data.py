from django.core.management.base import BaseCommand
from cars.models import (
    TransmissionType, CarStatus, BookingStatus,
    PaymentType, PaymentStatus, CarCategory, User
)


class Command(BaseCommand):
    help = 'Загрузка начальных данных в базу данных'

    def handle(self, *args, **kwargs):
        # Создаем типы трансмиссии
        transmissions = ['автомат', 'механика']
        for name in transmissions:
            TransmissionType.objects.get_or_create(name=name)
            self.stdout.write(f'Создан тип трансмиссии: {name}')

        # Создаем статусы автомобилей
        car_statuses = ['доступен', 'забронирован', 'на обслуживании', 'недоступен']
        for name in car_statuses:
            CarStatus.objects.get_or_create(name=name)
            self.stdout.write(f'Создан статус автомобиля: {name}')

        # Создаем статусы бронирований
        booking_statuses = ['подтверждено', 'активно', 'завершено', 'отменено']
        for name in booking_statuses:
            BookingStatus.objects.get_or_create(name=name)
            self.stdout.write(f'Создан статус бронирования: {name}')

        # Создаем типы платежей
        payment_types = ['предоплата', 'полная оплата', 'штраф', 'возврат']
        for name in payment_types:
            PaymentType.objects.get_or_create(name=name)
            self.stdout.write(f'Создан тип платежа: {name}')

        # Создаем статусы платежей
        payment_statuses = ['ожидает', 'успешен', 'неудачен', 'возвращен']
        for name in payment_statuses:
            PaymentStatus.objects.get_or_create(name=name)
            self.stdout.write(f'Создан статус платежа: {name}')

        # Создаем категории автомобилей
        categories = [
            ('Эконом', 'Бюджетные автомобили для городских поездок'),
            ('Комфорт', 'Автомобили среднего класса с повышенным комфортом'),
            ('Бизнес', 'Премиум автомобили для деловых поездок'),
            ('Внедорожник', 'Автомобили повышенной проходимости'),
            ('Премиум', 'Люкс автомобили')
        ]
        for name, description in categories:
            CarCategory.objects.get_or_create(name=name, defaults={'description': description})
            self.stdout.write(f'Создана категория: {name}')

        self.stdout.write(self.style.SUCCESS('Начальные данные успешно загружены!'))