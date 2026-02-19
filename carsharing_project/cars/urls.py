from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Основные маршруты
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('profile/', views.profile, name='profile'),

    # Автомобили
    path('cars/', views.car_list, name='car_list'),
    path('cars/<int:car_id>/', views.car_detail, name='car_detail'),
    path('cars/<int:car_id>/book/', views.book_car, name='book_car'),
    path('cars/<int:car_id>/check-availability/', views.check_availability, name='check_availability'),

    # Бронирования
    path('bookings/', views.my_bookings, name='my_bookings'),
    path('bookings/<int:booking_id>/', views.booking_detail, name='booking_detail'),
    path('bookings/<int:booking_id>/cancel/', views.cancel_booking, name='cancel_booking'),
    path('bookings/<int:booking_id>/review/', views.add_review, name='add_review'),

    # Административные маршруты (НАЧИНАЕМ С admin-panel/)
    path('admin-panel/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/cars/', views.manage_cars, name='manage_cars'),
    path('admin-panel/cars/add/', views.add_car, name='add_car'),
    path('admin-panel/cars/<int:car_id>/edit/', views.edit_car, name='edit_car'),
    path('admin-panel/cars/<int:car_id>/delete/', views.delete_car, name='delete_car'),
    path('admin-panel/bookings/', views.manage_bookings, name='manage_bookings'),
    path('admin-panel/bookings/<int:booking_id>/change-status/',
         views.change_booking_status, name='change_booking_status'),
    path('admin-panel/users/', views.manage_users, name='manage_users'),
    path('admin-panel/users/<int:user_id>/toggle-status/',
         views.toggle_user_status, name='toggle_user_status'),

    # Смена пароля (встроенные Django views)
    path('password-change/',
         auth_views.PasswordChangeView.as_view(template_name='cars/password_change.html'),
         name='password_change'),
    path('password-change/done/',
         auth_views.PasswordChangeDoneView.as_view(template_name='cars/password_change_done.html'),
         name='password_change_done'),
    # Маршруты для менеджера
    path('manager/dashboard/', views.manager_dashboard, name='manager_dashboard'),
    path('manager/bookings/', views.manager_bookings, name='manager_bookings'),
    path('manager/bookings/<int:booking_id>/', views.booking_detail, name='manager_booking_detail'),
    path('manager/bookings/<int:booking_id>/confirm/', views.confirm_booking, name='confirm_booking'),
    path('manager/bookings/<int:booking_id>/change-status/', views.change_booking_status, name='change_booking_status'),
    path('manager/cars/', views.manager_cars, name='manager_cars'),

    # Чат поддержки
    path('support/', views.support_chat_list, name='support_chat_list'),
    path('support/create/', views.support_create_chat, name='support_create_chat'),
    path('support/<int:chat_id>/', views.support_chat_detail, name='support_chat_detail'),
    path('support/<int:chat_id>/close/', views.support_close_chat, name='support_close_chat'),
        path('review/add/<int:booking_id>/', views.add_review, name='add_review'),
    # Маршруты для партнера
    path('partner/', views.partner_dashboard, name='partner_dashboard'),
    path('partner/become/', views.become_partner, name='become_partner'),
    path('partner/cars/', views.partner_cars, name='partner_cars'),
    path('partner/cars/add/', views.partner_add_car, name='partner_add_car'),
    path('partner/cars/<int:car_id>/edit/', views.partner_edit_car, name='partner_edit_car'),
    path('partner/cars/<int:car_id>/delete/', views.partner_delete_car, name='partner_delete_car'),
    path('partner/bookings/', views.partner_bookings, name='partner_bookings'),
    path('partner/bookings/<int:booking_id>/', views.partner_booking_detail, name='partner_booking_detail'),
    path('partner/finance/', views.partner_finance, name='partner_finance'),
    path('partner/finance/request-payout/', views.partner_request_payout, name='partner_request_payout'),
]