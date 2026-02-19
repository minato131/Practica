# cars/management/commands/create_groups.py

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from cars.models import Car, Booking, Review, SupportChat, SupportMessage, PartnerPayout, User


class Command(BaseCommand):
    help = 'Создание групп пользователей и назначение прав'

    def handle(self, *args, **options):
        self.stdout.write('Создание групп пользователей...')

        # Создаем группы
        admin_group, created = Group.objects.get_or_create(name='Администраторы')
        manager_group, created = Group.objects.get_or_create(name='Менеджеры')
        partner_group, created = Group.objects.get_or_create(name='Партнеры')
        client_group, created = Group.objects.get_or_create(name='Клиенты')

        self.stdout.write(self.style.SUCCESS('✓ Группы созданы'))

        # Очищаем старые права
        admin_group.permissions.clear()
        manager_group.permissions.clear()
        partner_group.permissions.clear()
        client_group.permissions.clear()

        # Получаем все permissions для моделей
        content_types = {
            'car': ContentType.objects.get_for_model(Car),
            'booking': ContentType.objects.get_for_model(Booking),
            'review': ContentType.objects.get_for_model(Review),
            'supportchat': ContentType.objects.get_for_model(SupportChat),
            'supportmessage': ContentType.objects.get_for_model(SupportMessage),
            'partnerpayout': ContentType.objects.get_for_model(PartnerPayout),
            'user': ContentType.objects.get_for_model(User),
        }

        # Права для Администраторов (полный доступ ко всему)
        admin_permissions = Permission.objects.all()
        admin_group.permissions.set(admin_permissions)
        self.stdout.write(self.style.SUCCESS('✓ Права администраторов назначены'))

        # Права для Менеджеров
        manager_permissions = []

        # Car - только просмотр
        manager_permissions.extend(Permission.objects.filter(
            content_type=content_types['car'],
            codename__in=['view_car']
        ))

        # Booking - полный доступ (просмотр, изменение, подтверждение)
        manager_permissions.extend(Permission.objects.filter(
            content_type=content_types['booking'],
            codename__in=['view_booking', 'change_booking']
        ))

        # Review - просмотр и модерация
        manager_permissions.extend(Permission.objects.filter(
            content_type=content_types['review'],
            codename__in=['view_review', 'change_review']
        ))

        # SupportChat - полный доступ
        manager_permissions.extend(Permission.objects.filter(
            content_type=content_types['supportchat'],
            codename__in=['view_supportchat', 'change_supportchat', 'add_supportchat']
        ))

        # SupportMessage - полный доступ
        manager_permissions.extend(Permission.objects.filter(
            content_type=content_types['supportmessage'],
            codename__in=['view_supportmessage', 'add_supportmessage', 'change_supportmessage']
        ))

        # User - только просмотр
        manager_permissions.extend(Permission.objects.filter(
            content_type=content_types['user'],
            codename__in=['view_user']
        ))

        manager_group.permissions.set(manager_permissions)
        self.stdout.write(self.style.SUCCESS('✓ Права менеджеров назначены'))

        # Права для Партнеров
        partner_permissions = []

        # Car - полный доступ к своим машинам (через has_module_permission в шаблоне)
        partner_permissions.extend(Permission.objects.filter(
            content_type=content_types['car'],
            codename__in=['view_car', 'add_car', 'change_car', 'delete_car']
        ))

        # Booking - просмотр своих бронирований
        partner_permissions.extend(Permission.objects.filter(
            content_type=content_types['booking'],
            codename__in=['view_booking']
        ))

        # Review - просмотр отзывов на свои авто
        partner_permissions.extend(Permission.objects.filter(
            content_type=content_types['review'],
            codename__in=['view_review']
        ))

        # PartnerPayout - просмотр и создание запросов
        partner_permissions.extend(Permission.objects.filter(
            content_type=content_types['partnerpayout'],
            codename__in=['view_partnerpayout', 'add_partnerpayout']
        ))

        partner_group.permissions.set(partner_permissions)
        self.stdout.write(self.style.SUCCESS('✓ Права партнеров назначены'))

        # Права для Клиентов (минимальные права)
        client_permissions = []

        # Car - только просмотр
        client_permissions.extend(Permission.objects.filter(
            content_type=content_types['car'],
            codename__in=['view_car']
        ))

        # Booking - просмотр своих бронирований
        client_permissions.extend(Permission.objects.filter(
            content_type=content_types['booking'],
            codename__in=['view_booking']
        ))

        # Review - добавление отзывов
        client_permissions.extend(Permission.objects.filter(
            content_type=content_types['review'],
            codename__in=['add_review', 'view_review']
        ))

        # SupportChat - полный доступ к своим чатам
        client_permissions.extend(Permission.objects.filter(
            content_type=content_types['supportchat'],
            codename__in=['add_supportchat', 'view_supportchat', 'change_supportchat']
        ))

        # SupportMessage - отправка сообщений
        client_permissions.extend(Permission.objects.filter(
            content_type=content_types['supportmessage'],
            codename__in=['add_supportmessage', 'view_supportmessage']
        ))

        client_group.permissions.set(client_permissions)
        self.stdout.write(self.style.SUCCESS('✓ Права клиентов назначены'))

        self.stdout.write(self.style.SUCCESS('\n✅ Все группы успешно созданы и настроены!'))
        self.stdout.write('\nГруппы:')
        self.stdout.write('  - Администраторы (полный доступ)')
        self.stdout.write('  - Менеджеры (управление бронированиями и чатами)')
        self.stdout.write('  - Партнеры (управление своими авто)')
        self.stdout.write('  - Клиенты (базовый доступ)')