from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('profile/', views.profile, name='profile'),

    path('cars/', views.car_list, name='car_list'),
    path('cars/<int:car_id>/', views.car_detail, name='car_detail'),
    path('cars/<int:car_id>/book/', views.book_car, name='book_car'),

    path('bookings/', views.my_bookings, name='my_bookings'),
    path('bookings/<int:booking_id>/', views.booking_detail, name='booking_detail'),
    path('bookings/<int:booking_id>/review/', views.add_review, name='add_review'),

    # Административные маршруты
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/cars/', views.manage_cars, name='manage_cars'),
    path('admin/bookings/', views.manage_bookings, name='manage_bookings'),
]