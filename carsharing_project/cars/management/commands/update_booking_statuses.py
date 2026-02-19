# cars/management/commands/update_booking_statuses.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from cars.models import Booking, BookingStatus, CarStatus


class Command(BaseCommand):
    help = 'Обновляет статусы бронирований: активные становятся завершенными'

    def handle(self, *args, **options):
        self.stdout.write('Начинаю обновление статусов бронирований...')

        try:
            # Получаем статусы
            completed_status = BookingStatus.objects.get(name='завершено')
            active_status = BookingStatus.objects.get(name='активно')
            available_status = CarStatus.objects.get(name='доступен')

            # Находим все активные бронирования, у которых дата окончания прошла
            expired_bookings = Booking.objects.filter(
                status=active_status,
                end_date__lt=timezone.now()
            )

            count = expired_bookings.count()
            for booking in expired_bookings:
                # Меняем статус бронирования на завершено
                booking.status = completed_status
                booking.save()

                # Меняем статус автомобиля на доступен
                car = booking.car
                car.status = available_status
                car.save()

                self.stdout.write(f'Бронирование #{booking.id} завершено')

            self.stdout.write(self.style.SUCCESS(f'Успешно завершено {count} бронирований'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ошибка: {str(e)}'))