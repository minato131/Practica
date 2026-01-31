from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
import datetime
from .models import *
from .forms import *


def home(request):
    cars = Car.objects.filter(status__name='доступен')[:6]
    categories = CarCategory.objects.all()

    # Простой поиск
    search_query = request.GET.get('search', '')
    if search_query:
        cars = cars.filter(
            Q(brand__icontains=search_query) |
            Q(model__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    context = {
        'cars': cars,
        'categories': categories,
        'search_query': search_query,
    }
    return render(request, 'cars/home.html', context)


def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Регистрация прошла успешно!')
            return redirect('home')
    else:
        form = UserRegisterForm()

    return render(request, 'cars/register.html', {'form': form})


def user_login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, 'Вход выполнен успешно!')
            return redirect('home')
        else:
            messages.error(request, 'Неверный email или пароль')

    return render(request, 'cars/login.html')


def user_logout(request):
    logout(request)
    messages.info(request, 'Вы вышли из системы')
    return redirect('home')


def car_list(request):
    cars = Car.objects.filter(status__name='доступен')

    # Фильтрация
    category_id = request.GET.get('category')
    if category_id:
        cars = cars.filter(category_id=category_id)

    # Сортировка
    sort_by = request.GET.get('sort', 'created_at')
    if sort_by == 'price_asc':
        cars = cars.order_by('price_per_hour')
    elif sort_by == 'price_desc':
        cars = cars.order_by('-price_per_hour')
    else:
        cars = cars.order_by('-created_at')

    categories = CarCategory.objects.all()
    context = {
        'cars': cars,
        'categories': categories,
    }
    return render(request, 'cars/car_list.html', context)


def car_detail(request, car_id):
    car = get_object_or_404(Car, id=car_id)

    # Проверка доступности на выбранные даты
    available = True
    if request.method == 'GET':
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')

        if start_date_str and end_date_str:
            try:
                start_date = datetime.datetime.fromisoformat(start_date_str)
                end_date = datetime.datetime.fromisoformat(end_date_str)

                # Проверяем пересечения с другими бронированиями
                overlapping_bookings = Booking.objects.filter(
                    car=car,
                    start_date__lt=end_date,
                    end_date__gt=start_date,
                    status__name__in=['подтверждено', 'активно']
                )
                available = not overlapping_bookings.exists()
            except ValueError:
                pass

    # Форма бронирования
    booking_form = None
    if request.user.is_authenticated:
        booking_form = BookingForm()

    context = {
        'car': car,
        'booking_form': booking_form,
        'available': available,
    }
    return render(request, 'cars/car_detail.html', context)


@login_required
def book_car(request, car_id):
    car = get_object_or_404(Car, id=car_id, status__name='доступен')

    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.client = request.user
            booking.car = car

            # Расчет стоимости
            duration = booking.end_date - booking.start_date
            hours = duration.total_seconds() / 3600

            if hours <= 24:
                price = car.price_per_hour * hours
            else:
                days = hours / 24
                price = car.price_per_day * days

            booking.calculated_price = round(price, 2)
            booking.save()

            # Обновляем статус автомобиля
            car.status = CarStatus.objects.get(name='забронирован')
            car.save()

            messages.success(request, f'Автомобиль успешно забронирован! Сумма: {booking.calculated_price} руб.')
            return redirect('booking_detail', booking_id=booking.id)

    return redirect('car_detail', car_id=car_id)


@login_required
def booking_detail(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, client=request.user)
    return render(request, 'cars/booking_detail.html', {'booking': booking})


@login_required
def my_bookings(request):
    bookings = Booking.objects.filter(client=request.user).order_by('-created_at')
    return render(request, 'cars/my_bookings.html', {'bookings': bookings})


@login_required
def profile(request):
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.phone = request.POST.get('phone', '')
        user.driver_license = request.POST.get('driver_license', '')
        user.save()
        messages.success(request, 'Профиль обновлен')
        return redirect('profile')

    return render(request, 'cars/profile.html')


@login_required
def add_review(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, client=request.user)

    # Проверяем, что бронирование завершено
    if booking.status.name != 'завершено':
        messages.error(request, 'Можно оставить отзыв только для завершенных бронирований')
        return redirect('my_bookings')

    # Проверяем, что отзыва еще нет
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
            return redirect('my_bookings')
    else:
        form = ReviewForm()

    context = {
        'form': form,
        'booking': booking,
    }
    return render(request, 'cars/add_review.html', context)


# Административные функции
def is_admin(user):
    return user.is_superuser


@user_passes_test(is_admin)
def admin_dashboard(request):
    stats = {
        'total_cars': Car.objects.count(),
        'available_cars': Car.objects.filter(status__name='доступен').count(),
        'total_bookings': Booking.objects.count(),
        'active_bookings': Booking.objects.filter(status__name='активно').count(),
        'total_users': User.objects.count(),
        'total_revenue': Booking.objects.aggregate(
            total=models.Sum('final_price')
        )['total'] or 0,
    }

    recent_bookings = Booking.objects.select_related('car', 'client').order_by('-created_at')[:10]

    context = {
        'stats': stats,
        'recent_bookings': recent_bookings,
    }
    return render(request, 'cars/admin/dashboard.html', context)


@user_passes_test(is_admin)
def manage_cars(request):
    cars = Car.objects.select_related('partner', 'category', 'status').all()
    return render(request, 'cars/admin/manage_cars.html', {'cars': cars})


@user_passes_test(is_admin)
def manage_bookings(request):
    bookings = Booking.objects.select_related('car', 'client', 'status').all()
    return render(request, 'cars/admin/manage_bookings.html', {'bookings': bookings})