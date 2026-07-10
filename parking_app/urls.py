from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Auth
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('password_change/', auth_views.PasswordChangeView.as_view(template_name='parking_app/password_change.html'), name='password_change'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(template_name='parking_app/password_change_done.html'), name='password_change_done'),

    # Main
    path('dashboard/', views.dashboard, name='dashboard'),
    path('my-reservations/', views.my_reservations, name='my_reservations'),
    path('wallet/', views.wallet, name='wallet'),
    path('profile/', views.profile, name='profile'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-overbooking/', views.overbooking_prevention_dashboard, name='overbooking_prevention_dashboard'),
    path('analytics/', views.analytics, name='analytics'),
    
    # Notifications
    path('notifications/', views.notifications_page, name='notifications_page'),
    path('api/notifications/', views.get_notifications, name='get_notifications'),
    path('api/notifications/<int:notification_id>/read/', views.mark_notification_as_read, name='mark_notification_as_read'),

    # Parking
    path('booking_map/', views.booking_map, name='booking_map'),
    path('reserve_spot/', views.reserve_spot, name='reserve_spot'),
    path('get_slots_json/', views.get_slots_json, name='get_slots_json'),
    path("live-slots/", views.live_slot_status, name="live_slots"),

    # Clean Booking Pipeline
    path('select-slot/', views.select_parking_slot, name='select_parking_slot'),
    path('reserve-booking/', views.reserve_booking, name='reserve_booking'),
    path('payment/<int:booking_id>/', views.payment_page, name='payment_page'),
    path('resume-payment/<int:booking_id>/', views.resume_payment, name='resume_payment'),
    path('quick-pay-wallet/<int:booking_id>/', views.quick_pay_wallet, name='quick_pay_wallet'),
    path('razorpay-checkout/<int:transaction_id>/', views.razorpay_checkout, name='razorpay_checkout'),
    path('wallet-payment/<int:transaction_id>/', views.wallet_payment, name='wallet_payment'),
    path('payment-success/<int:transaction_id>/', views.payment_success, name='payment_success'),
    path('booking-success/<int:booking_id>/', views.booking_success, name='booking_success'),
    path('booking-check-in/<int:booking_id>/', views.booking_check_in, name='booking_check_in'),
    path('booking-check-out/<int:booking_id>/', views.booking_check_out, name='booking_check_out'),
    path('booking-cancel/<int:booking_id>/', views.cancel_booking, name='cancel_booking'),
    
    # E-Tickets
    path('e-ticket/<int:ticket_id>/', views.view_e_ticket, name='view_e_ticket'),
    path('all-e-tickets/', views.all_e_tickets, name='all_e_tickets'),

    # Payment (Legacy)
    path("payment-legacy/<int:reservation_id>/", views.payment, name="payment"),
    
    # Check-in/Check-out
    path("check-in/<int:reservation_id>/", views.check_in, name="check_in"),
    path("check-out/<int:reservation_id>/", views.check_out, name="check_out"),
    path("cancel-reservation/<int:reservation_id>/", views.cancel_reservation, name="cancel_reservation"),

     path("nearest-parking/", views.nearest_parking, name="nearest_parking"),
     path("campus-map/", views.campus_map, name="campus_map"),

     # Advanced Predictions API
     path("api/predict-availability/", views.predict_availability_api, name="predict_availability_api"),
     path("api/forecast-24hours/", views.forecast_24hours_api, name="forecast_24hours_api"),
     path("api/parking-statistics/", views.parking_statistics_api, name="parking_statistics_api"),
     path("zone-availability/", views.zone_availability_dashboard, name="zone_availability_dashboard"),
     path("api/all-zones/", views.all_zones_json, name="all_zones_json"),
     path("parking-map/", views.parking_map_view, name="parking_map_view"),
     path("api/parking-map/", views.parking_map_api, name="parking_map_api"),

]
