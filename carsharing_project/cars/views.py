from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q, Count, Sum
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
import datetime
from .models import *
from .forms import *
from decimal import Decimal


# Главная страница
def home(request):
    cars = Car.objects.filter(status__name='доступен').order_by('-created_at')[:6]
    categories = CarCategory.objects.all()

    # Статистика для главной страницы
    stats = {
        'total_cars': Car.objects.count(),
        'total_bookings': Booking.objects.count(),
        'available_cars': Car.objects.filter(status__name='доступен').count(),
    }

    context = {
        'cars': cars,
        'categories': categories,
        'stats': stats,
    }
    return render(request, 'cars/home.html', context)


# Регистрация
def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Регистрация прошла успешно! Добро пожаловать!')
            return redirect('home')
    else:
        form = UserRegisterForm()

    return render(request, 'cars/register.html', {'form': form})


# Вход
def user_login(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f'Добро пожаловать, {user.first_name or user.email}!')

            # Перенаправление по роли
            next_url = request.GET.get('next', 'home')
            return redirect(next_url)
        else:
            messages.error(request, 'Неверный email или пароль')

    return render(request, 'cars/login.html')


# Выход
def user_logout(request):
    logout(request)
    messages.info(request, 'Вы успешно вышли из системы')
    return redirect('home')


# Каталог автомобилей
def car_list(request):
    cars = Car.objects.filter(status__name='доступен')

    # Фильтрация
    category_id = request.GET.get('category')
    transmission_id = request.GET.get('transmission')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    search = request.GET.get('search', '')

    if category_id and category_id != 'all':
        cars = cars.filter(category_id=category_id)

    if transmission_id and transmission_id != 'all':
        cars = cars.filter(transmission_id=transmission_id)

    if min_price:
        try:
            cars = cars.filter(price_per_hour__gte=float(min_price))
        except ValueError:
            pass

    if max_price:
        try:
            cars = cars.filter(price_per_hour__lte=float(max_price))
        except ValueError:
            pass

    if search:
        cars = cars.filter(
            Q(brand__icontains=search) |
            Q(model__icontains=search) |
            Q(description__icontains=search) |
            Q(address__icontains=search)
        )

    # Сортировка
    sort_by = request.GET.get('sort', 'newest')
    if sort_by == 'price_asc':
        cars = cars.order_by('price_per_hour')
    elif sort_by == 'price_desc':
        cars = cars.order_by('-price_per_hour')
    elif sort_by == 'year_desc':
        cars = cars.order_by('-year')
    else:
        cars = cars.order_by('-created_at')

    # Получаем все фильтры
    categories = CarCategory.objects.all()
    transmissions = TransmissionType.objects.all()

    context = {
        'cars': cars,
        'categories': categories,
        'transmissions': transmissions,
        'selected_category': category_id,
        'selected_transmission': transmission_id,
        'min_price': min_price,
        'max_price': max_price,
        'search_query': search,
        'sort_by': sort_by,
    }
    return render(request, 'cars/car_list.html', context)


# Детальная информация об автомобиле
def car_detail(request, car_id):
    car = get_object_or_404(Car, id=car_id)

    # Проверяем доступность на даты
    available_dates = []
    unavailable_dates = []
    today = timezone.now()
    # Получаем все бронирования автомобиля
    bookings = Booking.objects.filter(
        car=car,
        status__name__in=['подтверждено', 'активно']
    )

    for booking in bookings:
        # Добавляем даты бронирования как недоступные
        current_date = booking.start_date.date()
        end_date = booking.end_date.date()
        while current_date <= end_date:
            unavailable_dates.append(current_date.strftime('%Y-%m-%d'))
            current_date += datetime.timedelta(days=1)

    # Получаем отзывы
    reviews = Review.objects.filter(booking__car=car).select_related('booking__client')

    context = {
        'car': car,
        'reviews': reviews,
        'unavailable_dates': unavailable_dates,
    }
    return render(request, 'cars/car_detail.html', context)


# Бронирование автомобиля
@login_required
def book_car(request, car_id):
    car = get_object_or_404(Car, id=car_id)

    today = timezone.now()

    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.client = request.user
            booking.car = car

            # Расчет стоимости
            duration = booking.end_date - booking.start_date
            hours = duration.total_seconds() / 3600

            # ИСПРАВЛЕНИЕ 1: Преобразуем hours в Decimal для корректного умножения
            hours_decimal = Decimal(str(hours))

            if hours <= 24:
                # Умножаем Decimal на Decimal
                price = car.price_per_hour * hours_decimal
            else:
                days = hours / 24
                # Преобразуем days в Decimal
                days_decimal = Decimal(str(days))
                price = car.price_per_day * days_decimal

            booking.calculated_price = round(price, 2)

            # Проверяем доступность (статус "доступен")
            if car.status.name != 'доступен':
                messages.error(request, 'Автомобиль временно недоступен для бронирования')
                return redirect('car_detail', car_id=car.id)

            # Проверяем пересечения с другими бронированиями
            overlapping = Booking.objects.filter(
                car=car,
                start_date__lt=booking.end_date,
                end_date__gt=booking.start_date,
                status__name__in=['подтверждено', 'активно']
            ).exists()

            if overlapping:
                messages.error(request, 'Автомобиль недоступен на выбранные даты')
                return redirect('car_detail', car_id=car.id)

            try:
                # Получаем статус "подтверждено"
                confirmed_status = BookingStatus.objects.get(name='подтверждено')
                booking.status = confirmed_status
                booking.save()

                # Меняем статус автомобиля на "забронирован"
                booked_status = CarStatus.objects.get(name='забронирован')
                car.status = booked_status
                car.save()

                # Создаем платеж (предоплата)
                payment_type = PaymentType.objects.get(name='предоплата')
                payment_status = PaymentStatus.objects.get(name='ожидает')

                # ИСПРАВЛЕНИЕ 2: Преобразуем для предоплаты
                prepayment_percent = Decimal('0.3')  # Используем Decimal для процента
                prepayment_amount = booking.calculated_price * prepayment_percent

                Payment.objects.create(
                    booking=booking,
                    amount=prepayment_amount,
                    payment_type=payment_type,
                    status=payment_status
                )

                messages.success(request,
                                 f'Бронирование создано! Сумма: {booking.calculated_price} руб. Ожидайте подтверждения менеджером.')
                return redirect('booking_detail', booking_id=booking.id)

            except Exception as e:
                messages.error(request, f'Ошибка при создании бронирования: {str(e)}')
                return redirect('car_detail', car_id=car.id)
        else:
            # Если форма невалидна, показываем ошибки
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        # ИСПРАВЛЕНИЕ 3: Добавляем начальные значения для формы
        initial_data = {
            'car': car,
            'start_date': timezone.now(),
            'end_date': timezone.now() + timezone.timedelta(hours=1)
        }
        form = BookingForm(initial=initial_data)

    context = {
        'car': car,
        'form': form,
    }
    return render(request, 'cars/book_car.html', context)


# Мои бронирования
@login_required
def my_bookings(request):
    bookings = Booking.objects.filter(client=request.user).select_related(
        'car', 'status'
    ).order_by('-created_at')

    # Разделяем по статусам
    active_bookings = bookings.filter(status__name__in=['подтверждено', 'активно'])
    past_bookings = bookings.filter(status__name__in=['завершено', 'отменено'])

    context = {
        'active_bookings': active_bookings,
        'past_bookings': past_bookings,
    }
    return render(request, 'cars/my_bookings.html', context)


# Детали бронирования
@login_required
def booking_detail(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, client=request.user)
    payments = Payment.objects.filter(booking=booking)

    # Проверяем, можно ли оставить отзыв
    can_review = (booking.status.name == 'завершено' and
                  not hasattr(booking, 'review'))

    context = {
        'booking': booking,
        'payments': payments,
        'can_review': can_review,
    }
    return render(request, 'cars/booking_detail.html', context)


# Отмена бронирования
@login_required
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, client=request.user)

    # Используем or вместо списка
    if booking.status.name == 'подтверждено' or booking.status.name == 'активно':
        # Получаем статус "отменено"
        cancelled_status = BookingStatus.objects.get(name='отменено')
        booking.status = cancelled_status
        booking.save()

        # Освобождаем автомобиль
        available_status = CarStatus.objects.get(name='доступен')
        booking.car.status = available_status
        booking.car.save()

        messages.success(request, 'Бронирование успешно отменено')
    else:
        messages.error(request, 'Невозможно отменить это бронирование')

    return redirect('my_bookings')


# Профиль пользователя
@login_required
def profile(request):
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.phone = request.POST.get('phone', '')
        user.driver_license = request.POST.get('driver_license', '')
        user.save()

        messages.success(request, 'Профиль успешно обновлен')
        return redirect('profile')

    # Статистика пользователя
    user_stats = {
        'total_bookings': Booking.objects.filter(client=request.user).count(),
        'active_bookings': Booking.objects.filter(
            client=request.user,
            status__name__in=['подтверждено', 'активно']
        ).count(),
        'total_spent': Booking.objects.filter(
            client=request.user
        ).aggregate(total=Sum('final_price'))['total'] or 0,
    }

    context = {
        'user_stats': user_stats,
    }
    return render(request, 'cars/profile.html', context)


# Добавление отзыва
@login_required
def add_review(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, client=request.user)

    # Используем or вместо списка в проверках
    if booking.status.name != 'завершено':
        messages.error(request, 'Можно оставить отзыв только для завершенных бронирований')
        return redirect('my_bookings')

    if hasattr(booking, 'review'):
        messages.error(request, 'Вы уже оставили отзыв для этого бронирования')
        return redirect('my_bookings')

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.booking = booking
            review.save()
            messages.success(request, 'Спасибо за ваш отзыв!')
            return redirect('booking_detail', booking_id=booking.id)
    else:
        form = ReviewForm()

    context = {
        'form': form,
        'booking': booking,
    }
    return render(request, 'cars/add_review.html', context)


# ============ АДМИНИСТРАТИВНЫЕ ФУНКЦИИ ============

def is_admin(user):
    return user.is_superuser


# Панель управления
@user_passes_test(is_admin)
def admin_dashboard(request):
    # Статистика
    stats = {
        'total_cars': Car.objects.count(),
        'available_cars': Car.objects.filter(status__name='доступен').count(),
        'booked_cars': Car.objects.filter(status__name='забронирован').count(),
        'total_bookings': Booking.objects.count(),
        'active_bookings': Booking.objects.filter(status__name='активно').count(),
        'completed_bookings': Booking.objects.filter(status__name='завершено').count(),
        'total_users': User.objects.count(),
        'total_partners': User.objects.filter(cars__isnull=False).distinct().count(),
        'total_revenue': Booking.objects.aggregate(total=Sum('final_price'))['total'] or 0,
    }

    # Последние бронирования
    recent_bookings = Booking.objects.select_related(
        'car', 'client', 'status'
    ).order_by('-created_at')[:10]

    # Последние автомобили
    recent_cars = Car.objects.select_related('partner', 'category').order_by('-created_at')[:10]

    context = {
        'stats': stats,
        'recent_bookings': recent_bookings,
        'recent_cars': recent_cars,
    }
    return render(request, 'cars/admin/dashboard.html', context)

# Управление автомобилями
@user_passes_test(is_admin)
def manage_cars(request):
    cars = Car.objects.select_related('partner', 'category', 'status', 'transmission').all()

    # Фильтрация
    status_filter = request.GET.get('status')
    category_filter = request.GET.get('category')

    if status_filter and status_filter != 'all':
        cars = cars.filter(status_id=status_filter)

    if category_filter and category_filter != 'all':
        cars = cars.filter(category_id=category_filter)

    # Получаем фильтры
    statuses = CarStatus.objects.all()
    categories = CarCategory.objects.all()

    # Подсчет статистики
    total_cars = cars.count()
    available_count = 0
    booked_count = 0

    for car in cars:
        if car.status.name == 'доступен':
            available_count += 1
        elif car.status.name == 'забронирован':
            booked_count += 1

    context = {
        'cars': cars,
        'statuses': statuses,
        'categories': categories,
        'selected_status': status_filter,
        'selected_category': category_filter,
        'total_cars': total_cars,
        'available_count': available_count,
        'booked_count': booked_count,
    }
    return render(request, 'cars/admin/manage_cars.html', context)


# Добавление автомобиля
@user_passes_test(is_admin)
def add_car(request):
    if request.method == 'POST':
        form = CarForm(request.POST, request.FILES)
        if form.is_valid():
            car = form.save(commit=False)
            car.partner = request.user
            # Получаем статус "доступен"
            available_status = CarStatus.objects.get(name='доступен')
            car.status = available_status
            car.save()
            messages.success(request, 'Автомобиль успешно добавлен')
            return redirect('manage_cars')
    else:
        form = CarForm()

    context = {
        'form': form,
    }
    return render(request, 'cars/admin/add_car.html', context)


# Редактирование автомобиля
@user_passes_test(is_admin)
def edit_car(request, car_id):
    car = get_object_or_404(Car, id=car_id)

    if request.method == 'POST':
        form = CarForm(request.POST, request.FILES, instance=car)
        if form.is_valid():
            form.save()
            messages.success(request, 'Автомобиль успешно обновлен')
            return redirect('manage_cars')
    else:
        form = CarForm(instance=car)

    context = {
        'form': form,
        'car': car,
    }
    return render(request, 'cars/admin/edit_car.html', context)


# Удаление автомобиля
@user_passes_test(is_admin)
def delete_car(request, car_id):
    car = get_object_or_404(Car, id=car_id)

    if request.method == 'POST':
        car.delete()
        messages.success(request, 'Автомобиль успешно удален')
        return redirect('manage_cars')

    context = {
        'car': car,
    }
    return render(request, 'cars/admin/delete_car.html', context)


# Управление бронированиями
@user_passes_test(is_admin)
def manage_bookings(request):
    bookings = Booking.objects.select_related('car', 'client', 'status').all()

    # Фильтрация
    status_filter = request.GET.get('status')

    if status_filter and status_filter != 'all':
        bookings = bookings.filter(status_id=status_filter)

    # Получаем фильтры
    statuses = BookingStatus.objects.all()

    # Подсчет статистики
    total_bookings = bookings.count()
    active_count = 0
    confirmed_count = 0
    completed_count = 0

    for booking in bookings:
        if booking.status.name == 'активно':
            active_count += 1
        elif booking.status.name == 'подтверждено':
            confirmed_count += 1
        elif booking.status.name == 'завершено':
            completed_count += 1

    context = {
        'bookings': bookings,
        'statuses': statuses,
        'selected_status': status_filter,
        'total_bookings': total_bookings,
        'active_count': active_count,
        'confirmed_count': confirmed_count,
        'completed_count': completed_count,
    }
    return render(request, 'cars/admin/manage_bookings.html', context)


# Изменение статуса бронирования
@user_passes_test(is_admin)
def change_booking_status(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    if request.method == 'POST':
        new_status_id = request.POST.get('status')
        new_status = get_object_or_404(BookingStatus, id=new_status_id)

        booking.status = new_status

        # Если статус меняется на "завершено" или "отменено", освобождаем автомобиль
        if new_status.name in ['завершено', 'отменено']:
            booking.car.status = CarStatus.objects.get(name='доступен')
            booking.car.save()
        elif new_status.name == 'активно':
            booking.car.status = CarStatus.objects.get(name='забронирован')
            booking.car.save()

        booking.save()
        messages.success(request, f'Статус бронирования изменен на "{new_status.name}"')

    return redirect('manage_bookings')


# Управление пользователями
@user_passes_test(is_admin)
def manage_users(request):
    users = User.objects.all().order_by('-date_joined')

    # Подсчет статистики
    total_users = users.count()
    admin_count = 0
    staff_count = 0
    client_count = 0

    for user_obj in users:
        if user_obj.is_superuser:
            admin_count += 1
        elif user_obj.is_staff:
            staff_count += 1
        else:
            client_count += 1

    context = {
        'users': users,
        'total_users': total_users,
        'admin_count': admin_count,
        'staff_count': staff_count,
        'client_count': client_count,
    }
    return render(request, 'cars/admin/manage_users.html', context)


# Изменение статуса пользователя
@user_passes_test(is_admin)
def toggle_user_status(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'toggle_staff':
            user.is_staff = not user.is_staff
            user.save()
            status = "сотрудником" if user.is_staff else "пользователем"
            messages.success(request, f'Пользователь теперь {status}')
        elif action == 'toggle_active':
            user.is_active = not user.is_active
            user.save()
            status = "активирован" if user.is_active else "деактивирован"
            messages.success(request, f'Пользователь {status}')

    return redirect('manage_users')


# API для проверки доступности
def check_availability(request, car_id):
    car = get_object_or_404(Car, id=car_id)

    if request.method == 'GET':
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')

        if start_date_str and end_date_str:
            try:
                start_date = datetime.datetime.fromisoformat(start_date_str)
                end_date = datetime.datetime.fromisoformat(end_date_str)

                # Проверяем пересечения
                overlapping = Booking.objects.filter(
                    car=car,
                    start_date__lt=end_date,
                    end_date__gt=start_date,
                    status__name__in=['подтверждено', 'активно']
                ).exists()

                available = not overlapping

                # Расчет стоимости
                duration = end_date - start_date
                hours = duration.total_seconds() / 3600

                if hours <= 24:
                    price = car.price_per_hour * hours
                else:
                    days = hours / 24
                    price = car.price_per_day * days

                return JsonResponse({
                    'available': available,
                    'price': round(price, 2),
                    'duration_hours': round(hours, 1),
                })
            except ValueError:
                return JsonResponse({'error': 'Invalid date format'}, status=400)

    return JsonResponse({'error': 'Missing parameters'}, status=400)


# Страница бронирования (отдельная)
@login_required
def book_car_page(request, car_id):
    car = get_object_or_404(Car, id=car_id)
    form = BookingForm()

    context = {
        'car': car,
        'form': form,
    }
    return render(request, 'cars/book_car.html', context)


# Добавим проверки для разных ролей
def is_admin(user):
    return user.is_superuser


def is_manager(user):
    return user.is_staff and not user.is_superuser


def is_manager_or_admin(user):
    return user.is_staff


# Обновим представления для менеджера
@user_passes_test(is_manager_or_admin)
def manager_dashboard(request):
    """Дашборд для менеджера"""
    # Статистика для менеджера
    stats = {
        'total_bookings': Booking.objects.count(),
        'pending_bookings': Booking.objects.filter(status__name='подтверждено').count(),
        'active_bookings': Booking.objects.filter(status__name='активно').count(),
        'today_bookings': Booking.objects.filter(
            start_date__date=datetime.datetime.now().date()
        ).count(),
    }

    # Последние бронирования
    recent_bookings = Booking.objects.select_related(
        'car', 'client', 'status'
    ).order_by('-created_at')[:10]

    # Бронирования, требующие внимания
    pending_bookings = Booking.objects.filter(
        status__name='подтверждено'
    ).select_related('car', 'client').order_by('start_date')[:5]

    context = {
        'stats': stats,
        'recent_bookings': recent_bookings,
        'pending_bookings': pending_bookings,
    }
    return render(request, 'cars/manager/dashboard.html', context)


@user_passes_test(is_manager_or_admin)
def manager_bookings(request):
    """Управление бронированиями для менеджера"""
    bookings = Booking.objects.select_related('car', 'client', 'status').all()

    # Фильтрация
    status_filter = request.GET.get('status')

    if status_filter and status_filter != 'all':
        bookings = bookings.filter(status_id=status_filter)

    # Получаем фильтры
    statuses = BookingStatus.objects.all()

    # Подсчет статистики
    total_bookings = bookings.count()
    active_count = 0
    confirmed_count = 0
    completed_count = 0

    for booking in bookings:
        if booking.status.name == 'активно':
            active_count += 1
        elif booking.status.name == 'подтверждено':
            confirmed_count += 1
        elif booking.status.name == 'завершено':
            completed_count += 1

    context = {
        'bookings': bookings,
        'statuses': statuses,
        'selected_status': status_filter,
        'total_bookings': total_bookings,
        'active_count': active_count,
        'confirmed_count': confirmed_count,
        'completed_count': completed_count,
    }
    return render(request, 'cars/manager/bookings.html', context)


@user_passes_test(is_manager_or_admin)
def confirm_booking(request, booking_id):
    """Подтверждение бронирования менеджером"""
    booking = get_object_or_404(Booking, id=booking_id)

    if request.method == 'POST':
        # Получаем статус "активно"
        active_status = BookingStatus.objects.get(name='активно')
        booking.status = active_status
        booking.save()

        # Меняем статус автомобиля
        booked_status = CarStatus.objects.get(name='забронирован')
        booking.car.status = booked_status
        booking.car.save()

        messages.success(request, f'Бронирование #{booking.id} успешно подтверждено!')
        return redirect('manager_bookings')

    context = {
        'booking': booking,
    }
    return render(request, 'cars/manager/confirm_booking.html', context)


@user_passes_test(is_manager_or_admin)
def manager_cars(request):
    """Просмотр автомобилей для менеджера (только просмотр)"""
    cars = Car.objects.select_related('partner', 'category', 'status', 'transmission').all()

    # Фильтрация
    status_filter = request.GET.get('status')
    category_filter = request.GET.get('category')

    if status_filter and status_filter != 'all':
        cars = cars.filter(status_id=status_filter)

    if category_filter and category_filter != 'all':
        cars = cars.filter(category_id=category_filter)

    # Получаем фильтры
    statuses = CarStatus.objects.all()
    categories = CarCategory.objects.all()

    # Подсчет статистики
    total_cars = cars.count()
    available_count = 0
    booked_count = 0

    for car in cars:
        if car.status.name == 'доступен':
            available_count += 1
        elif car.status.name == 'забронирован':
            booked_count += 1

    context = {
        'cars': cars,
        'statuses': statuses,
        'categories': categories,
        'selected_status': status_filter,
        'selected_category': category_filter,
        'total_cars': total_cars,
        'available_count': available_count,
        'booked_count': booked_count,
    }
    return render(request, 'cars/manager/cars.html', context)