import datetime
import math

from django.contrib import messages
from django.db import models
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.conf import settings

from .models import (
    ParkingLot,
    ParkingSlot,
    Reservation,
    Profile,
    ParkingMonitor,
    AdypuUser,
    Booking,
    Transaction,
    Refund,
    ETicket,
)

from .predictor import predict_slot_availability
from .utils_slots import get_best_available_slot
from .email_notifications import (
    send_reservation_confirmation,
    send_payment_confirmation,
)
from .notifications import (
    create_reservation_notification,
    create_payment_notification,
    create_check_in_notification,
    create_check_out_notification,
)
from .qr_code_utils import generate_qr_code_base64
import secrets
try:
    from .advanced_predictor import (
        get_availability_prediction,
        get_24hour_forecast,
    )
except (ImportError, ModuleNotFoundError):
    from .simple_predictor import (
        get_availability_prediction,
        get_24hour_forecast,
    )


# ==========================
# 🏠 LOGIN / LOGOUT
# ==========================
def login_view(request):
    if request.method == "POST":
        user = authenticate(
            request,
            username=request.POST.get("username"),
            password=request.POST.get("password"),
        )
        if user:
            login(request, user)
            return redirect("dashboard")
        messages.error(request, "Invalid username or password.")
    return render(request, "registration/login.html")


@login_required
def logout_view(request):
    logout(request)
    return redirect("login")


# ==========================
# 📝 REGISTER
# ==========================
def register_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")
        phone = request.POST.get("phone")

        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return redirect("register")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect("register")

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1
        )

        Profile.objects.create(user=user, phone=phone)

        messages.success(request, "Account created successfully. Please login.")
        return redirect("login")

    return render(request, "registration/register.html")


# ==========================
# 👤 PROFILE
# ==========================
@login_required
def profile(request):
    profile = get_object_or_404(Profile, user=request.user)

    if request.method == "POST":
        profile.phone = request.POST.get("phone")
        profile.wallet_inr = request.POST.get("wallet_inr")
        if request.FILES.get("profile_image"):
            profile.profile_image = request.FILES["profile_image"]
        profile.save()
        return redirect("profile")

    return render(request, "parking_app/profile.html", {"profile": profile})


# ==========================
# 💰 WALLET
# ==========================
@login_required
def wallet(request):
    return render(
        request,
        "parking_app/wallet.html",
        {"balance": request.user.profile.wallet_inr}
    )


# ==========================
# 🗺️ BOOKING MAP
# ==========================
@login_required
def booking_map(request):
    occupied = ParkingSlot.objects.filter(is_occupied=True).count()
    total = ParkingSlot.objects.count()
    
    assigned_slot = None
    if total > 0:
        assigned_slot = get_best_available_slot("car")
    
    return render(request, "parking_app/booking_map.html", {
        "assigned_slot": assigned_slot,
    })


# ==========================
# 🎫 HELPER: Generate E-Ticket
# ==========================
def generate_e_ticket(booking):
    ticket_number = f"TKT{booking.id}{secrets.token_hex(4).upper()}"
    qr_data = f"eticket:{booking.id}:{ticket_number}:{booking.user.id}"
    qr_code = generate_qr_code_base64(qr_data)
    
    e_ticket, created = ETicket.objects.get_or_create(
        booking=booking,
        defaults={
            'user': booking.user,
            'ticket_number': ticket_number,
            'qr_code': qr_code,
            'status': 'valid'
        }
    )
    return e_ticket


# ==========================
# ✨ CLEAN BOOKING PIPELINE
# ==========================
@login_required
def select_parking_slot(request):
    if request.method == "POST":
        vehicle_number = request.POST.get("vehicle_number", "").strip()
        vehicle_type = request.POST.get("vehicle_type", "car").strip()
        slot_id = request.POST.get("slot_id")
        
        if not vehicle_number:
            return JsonResponse({"status": "error", "message": "Vehicle number required"}, status=400)
        
        if not slot_id:
            return JsonResponse({"status": "error", "message": "Slot selection required"}, status=400)
        
        try:
            slot = ParkingSlot.objects.get(id=slot_id)
            if slot.is_occupied:
                return JsonResponse({"status": "error", "message": "Slot no longer available"}, status=400)
        except ParkingSlot.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Invalid slot"}, status=400)
        
        request.session['slot_selection'] = {
            'slot_id': slot_id,
            'slot_number': slot.slot_number,
            'vehicle_number': vehicle_number,
            'vehicle_type': vehicle_type,
        }
        
        return JsonResponse({"status": "success", "redirect": "reserve_booking"})
    
    available_slots = ParkingSlot.objects.filter(is_occupied=False)
    occupied_count = ParkingSlot.objects.filter(is_occupied=True).count()
    total_count = ParkingSlot.objects.count()
    
    return render(request, "parking_app/select_slot.html", {
        "available_slots": available_slots,
        "occupancy_rate": (occupied_count / max(1, total_count)) * 100,
    })


@login_required
def reserve_booking(request):
    if request.method == "POST":
        start_time_str = request.POST.get("start_time")
        end_time_str = request.POST.get("end_time")
        
        selection = request.session.get('slot_selection')
        if not selection:
            messages.error(request, "Please select a slot first")
            return redirect("select_parking_slot")
        
        try:
            start_time = datetime.datetime.fromisoformat(start_time_str)
            end_time = datetime.datetime.fromisoformat(end_time_str)
            
            start_time = timezone.make_aware(start_time)
            end_time = timezone.make_aware(end_time)
        except (ValueError, TypeError):
            messages.error(request, "Invalid date/time format")
            return redirect("reserve_booking")
        
        if start_time >= end_time:
            messages.error(request, "End time must be after start time")
            return redirect("reserve_booking")
        
        slot = ParkingSlot.objects.get(id=selection['slot_id'])
        if slot.is_occupied:
            messages.error(request, "Selected slot is no longer available")
            del request.session['slot_selection']
            return redirect("select_parking_slot")
        
        base_price = 50
        demand = ParkingSlot.objects.filter(is_occupied=True).count() / max(1, ParkingSlot.objects.count())
        base_amount = round(base_price * (1 + demand), 2)
        
        booking = Booking.objects.create(
            user=request.user,
            slot=slot,
            vehicle_number=selection['vehicle_number'],
            vehicle_type=selection['vehicle_type'],
            start_time=start_time,
            end_time=end_time,
            base_amount=base_amount,
            status='reserved',
            reserved_at=timezone.now(),
            expires_at=timezone.now() + datetime.timedelta(minutes=15)
        )
        
        request.session['booking_id'] = booking.id
        del request.session['slot_selection']
        
        return redirect("payment_page", booking_id=booking.id)
    
    selection = request.session.get('slot_selection')
    if not selection:
        messages.error(request, "Please select a slot first")
        return redirect("select_parking_slot")
    
    return render(request, "parking_app/reserve_booking.html", {
        "slot_number": selection['slot_number'],
        "vehicle_number": selection['vehicle_number'],
        "vehicle_type": selection['vehicle_type'],
    })


@login_required
def payment_page(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    
    if booking.status not in ['reserved', 'pending']:
        messages.error(request, "Invalid booking status for payment")
        return redirect("dashboard")
    
    if booking.expires_at and booking.expires_at < timezone.now():
        booking.status = 'expired'
        booking.save()
        booking.slot.is_occupied = False
        booking.slot.save()
        messages.error(request, "Booking expired. Please start over.")
        return redirect("select_parking_slot")
    
    if request.method == "POST":
        payment_method = request.POST.get("payment_method", "razorpay")
        
        transaction = Transaction.objects.create(
            booking=booking,
            user=request.user,
            amount=booking.base_amount,
            gateway=payment_method,
            status='initiated'
        )
        
        request.session['transaction_id'] = transaction.id
        
        if payment_method == 'razorpay':
            return redirect("razorpay_checkout", transaction_id=transaction.id)
        elif payment_method == 'wallet':
            return redirect("wallet_payment", transaction_id=transaction.id)
        else:
            return redirect("paypal_checkout", transaction_id=transaction.id)
    
    return render(request, "parking_app/payment.html", {
        "booking": booking,
        "amount": booking.base_amount,
        "reservation": booking,
    })


@login_required
def razorpay_checkout(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id, user=request.user)
    
    if transaction.status != 'initiated':
        messages.error(request, "Invalid transaction state")
        return redirect("payment_page", booking_id=transaction.booking.id)
    
    try:
        from .payment_gateways import RazorpayPaymentGateway
        gateway = RazorpayPaymentGateway()
        order = gateway.create_order(transaction.booking, transaction.amount)
        
        if not order:
            transaction.status = 'failed'
            transaction.error_message = 'Failed to create Razorpay order'
            transaction.save()
            messages.error(request, "Failed to initialize payment")
            return redirect("payment_page", booking_id=transaction.booking.id)
        
        transaction.gateway_order_id = order['id']
        transaction.status = 'pending'
        transaction.save()
        
        return render(request, "parking_app/razorpay_checkout.html", {
            "transaction": transaction,
            "order": order,
            "key_id": settings.RAZORPAY_KEY_ID,
        })
    except Exception as e:
        transaction.status = 'failed'
        transaction.error_message = str(e)
        transaction.save()
        messages.error(request, f"Payment initialization failed: {str(e)}")
        return redirect("payment_page", booking_id=transaction.booking.id)


@login_required
def wallet_payment(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id, user=request.user)
    
    if transaction.status != 'initiated':
        messages.error(request, "Invalid transaction state")
        return redirect("payment_page", booking_id=transaction.booking.id)
    
    profile = request.user.profile
    
    if profile.wallet_inr < transaction.amount:
        messages.error(request, f"Insufficient wallet balance. Required: ₹{transaction.amount}, Available: ₹{profile.wallet_inr}")
        return redirect("payment_page", booking_id=transaction.booking.id)
    
    profile.wallet_inr -= transaction.amount
    profile.save()
    
    transaction.status = 'completed'
    transaction.gateway_payment_id = f'wallet_{transaction.id}'
    transaction.completed_at = timezone.now()
    transaction.save()
    
    booking = transaction.booking
    booking.status = 'confirmed'
    booking.confirmed_at = timezone.now()
    booking.slot.is_occupied = True
    booking.save()
    booking.slot.save()
    
    # Generate e-ticket
    e_ticket = generate_e_ticket(booking)
    
    # Schedule SMS reminder 10 minutes before booking ends
    from .tasks import send_booking_reminder_sms
    from datetime import datetime, timedelta
    
    reminder_time = booking.end_time - timedelta(minutes=10)
    now = timezone.now()
    
    if reminder_time > now:
        # Calculate delay in seconds until 10 minutes before end time
        delay_seconds = (reminder_time - now).total_seconds()
        
        # Schedule the SMS to be sent
        send_booking_reminder_sms.apply_async(
            args=[booking.id],
            countdown=delay_seconds
        )
        
        # Mark that reminder has been scheduled
        booking.reminder_sent = True
        booking.save()
    
    messages.success(request, f"✅ Payment successful! Slot #{booking.slot.slot_number} is confirmed for you. You'll receive an SMS 10 minutes before your parking time ends.")
    return redirect("view_e_ticket", ticket_id=e_ticket.id)


@login_required
def payment_success(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id, user=request.user)
    
    if transaction.status == 'completed':
        booking = transaction.booking
        booking.status = 'confirmed'
        booking.confirmed_at = timezone.now()
        booking.slot.is_occupied = True
        booking.save()
        booking.slot.save()
        
        e_ticket = generate_e_ticket(booking)
        
        # Schedule SMS reminder 10 minutes before booking ends
        from .tasks import send_booking_reminder_sms
        from datetime import datetime, timedelta
        
        reminder_time = booking.end_time - timedelta(minutes=10)
        now = timezone.now()
        
        if reminder_time > now:
            # Calculate delay in seconds until 10 minutes before end time
            delay_seconds = (reminder_time - now).total_seconds()
            
            # Schedule the SMS to be sent
            send_booking_reminder_sms.apply_async(
                args=[booking.id],
                countdown=delay_seconds
            )
            
            # Mark that reminder has been scheduled
            booking.reminder_sent = True
            booking.save()
        
        messages.success(request, f"✅ Payment Successful! Slot #{booking.slot.slot_number} is confirmed for you. You'll receive an SMS 10 minutes before your parking time ends.")
        return redirect("view_e_ticket", ticket_id=e_ticket.id)
    
    messages.error(request, "Payment verification failed")
    return redirect("payment_page", booking_id=transaction.booking.id)


@login_required
def booking_success(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    
    if booking.status != 'confirmed':
        messages.error(request, "Booking not confirmed")
        return redirect("dashboard")
    
    e_ticket = generate_e_ticket(booking)
    messages.success(request, f"✅ Booking Successful! Slot #{booking.slot.slot_number} is confirmed for you.")
    return redirect("view_e_ticket", ticket_id=e_ticket.id)


@login_required
def resume_payment(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    
    if booking.status != 'reserved':
        messages.error(request, "This booking is not pending payment")
        return redirect("dashboard")
    
    if booking.expires_at and booking.expires_at < timezone.now():
        booking.status = 'expired'
        booking.save()
        booking.slot.is_occupied = False
        booking.slot.save()
        messages.error(request, "Booking expired. Please make a new booking.")
        return redirect("dashboard")
    
    return redirect("payment_page", booking_id=booking_id)


@login_required
def quick_pay_wallet(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    
    if booking.status != 'reserved':
        return JsonResponse({"status": "error", "message": "Booking not pending payment"}, status=400)
    
    profile = request.user.profile
    
    if profile.wallet_inr < booking.base_amount:
        return JsonResponse({
            "status": "error", 
            "message": f"Insufficient balance. Need ₹{booking.base_amount}, Have ₹{profile.wallet_inr}"
        }, status=400)
    
    profile.wallet_inr -= booking.base_amount
    profile.save()
    
    transaction = Transaction.objects.create(
        booking=booking,
        user=request.user,
        amount=booking.base_amount,
        gateway='wallet',
        status='completed',
        gateway_payment_id=f'wallet_{booking.id}',
        completed_at=timezone.now()
    )
    
    booking.status = 'confirmed'
    booking.confirmed_at = timezone.now()
    booking.slot.is_occupied = True
    booking.save()
    booking.slot.save()
    
    try:
        from .email_notifications import send_transaction_success_alert
        send_transaction_success_alert(transaction)
    except Exception as e:
        print(f"Error sending payment email: {e}")
    
    try:
        from .sms_notifications import send_transaction_success_sms
        send_transaction_success_sms(transaction)
    except Exception as e:
        print(f"Error sending payment SMS: {e}")
    
    return JsonResponse({
        "status": "success",
        "message": "Payment completed via wallet",
        "booking_id": booking.id,
        "redirect": f"/booking-success/{booking.id}/"
    })


@login_required
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    
    if booking.status not in ['pending', 'reserved', 'confirmed']:
        messages.error(request, "Only pending, reserved or confirmed bookings can be cancelled")
        return redirect("dashboard")
    
    if request.method == "POST":
        reason = request.POST.get("reason", "User requested cancellation")
        
        transaction = getattr(booking, 'transaction', None)
        refund_amount = booking.base_amount if transaction and transaction.status == 'completed' else 0
        
        refund = Refund.objects.create(
            booking=booking,
            transaction=transaction,
            user=request.user,
            refund_amount=refund_amount,
            reason=reason,
            status='initiated'
        )
        
        booking.status = 'cancelled'
        booking.save()
        
        booking.slot.is_occupied = False
        booking.slot.save()
        
        if refund_amount > 0:
            try:
                if transaction.gateway == 'wallet':
                    profile = request.user.profile
                    profile.wallet_inr += refund_amount
                    profile.save()
                    refund.status = 'completed'
                    refund.completed_at = timezone.now()
                    refund.save()
                elif transaction.gateway == 'razorpay':
                    from .payment_gateways import RazorpayPaymentGateway
                    gateway = RazorpayPaymentGateway()
                    refund_response = gateway.client.payment.refund(
                        transaction.gateway_payment_id,
                        {'amount': int(refund_amount * 100)}
                    )
                    if refund_response:
                        refund.status = 'completed'
                        refund.gateway_refund_id = refund_response.get('id')
                        refund.completed_at = timezone.now()
                        refund.save()
            except Exception as e:
                refund.status = 'failed'
                refund.save()
                print(f"Error processing refund: {e}")
        
        try:
            from .email_notifications import send_booking_expiration_alert
            send_booking_expiration_alert(booking)
        except Exception as e:
            print(f"Error sending cancellation email: {e}")
        
        try:
            from .sms_notifications import send_cancellation_confirmation_sms
            send_cancellation_confirmation_sms(booking, refund_amount)
        except Exception as e:
            print(f"Error sending cancellation SMS: {e}")
        
        messages.success(request, f"✅ Booking cancelled. Refund of ₹{refund_amount} will be processed.")
        return redirect("dashboard")
    
    transaction = getattr(booking, 'transaction', None)
    refund_amount = booking.base_amount if transaction and transaction.status == 'completed' else 0
    
    return render(request, "parking_app/cancel_booking.html", {
        "booking": booking,
        "refund_amount": refund_amount,
    })


# ==========================
# 🚗 RESERVE SLOT (FINAL – DB + ML)
# ==========================
@login_required
def reserve_spot(request):
    if request.method == "GET":
        vehicle_number = request.GET.get("vehicle_number", "").strip()
        if not vehicle_number:
            return redirect("booking_map")

        occupied = ParkingSlot.objects.filter(is_occupied=True).count()
        total = ParkingSlot.objects.count()
        
        if total == 0:
            available_spots = []
        else:
            available_spots = ParkingSlot.objects.filter(is_occupied=False)

        prediction = None
        if total > 0:
            prediction = predict_slot_availability(
                hour=timezone.now().hour,
                weekday=timezone.now().weekday(),
                occupied=occupied,
                total=total,
                vehicle_type="car"
            )

        return render(request, "parking_app/reserve_spot.html", {
            "available_spots": available_spots,
            "prediction": prediction,
            "vehicle_number": vehicle_number,
            "wallet": request.user.profile,
        })

    vehicle_number = request.POST.get("vehicle_number", "").strip()
    vehicle_type = request.POST.get("vehicle_type", "").strip()
    start_time_str = request.POST.get("start_time", "").strip()
    end_time_str = request.POST.get("end_time", "").strip()
    slot_number = request.POST.get("slot_number", "").strip()
    slot_id = request.POST.get("slot_id", "").strip()
    amount = request.POST.get("amount", "50").strip()

    if not vehicle_number:
        messages.error(request, "🚫 Vehicle number is required.")
        return redirect("booking_map")

    if not vehicle_type:
        messages.error(request, "🚫 Vehicle type is required.")
        return redirect("booking_map")

    if not start_time_str or not end_time_str:
        messages.error(request, "🚫 Start and end times are required.")
        return redirect("booking_map")

    try:
        start_time = datetime.datetime.fromisoformat(start_time_str)
        end_time = datetime.datetime.fromisoformat(end_time_str)
        
        start_time = timezone.make_aware(start_time)
        end_time = timezone.make_aware(end_time)
    except (ValueError, TypeError):
        messages.error(request, "🚫 Invalid date/time format.")
        return redirect("booking_map")

    if start_time >= end_time:
        messages.error(request, "🚫 End time must be after start time.")
        return redirect("booking_map")

    if slot_id:
        try:
            slot = ParkingSlot.objects.get(id=slot_id)
            if slot.is_occupied:
                messages.error(request, "🚫 Selected slot is no longer available.")
                return redirect("booking_map")
        except ParkingSlot.DoesNotExist:
            messages.error(request, "🚫 Invalid slot ID.")
            return redirect("booking_map")
    elif slot_number:
        slots = ParkingSlot.objects.filter(slot_number=slot_number)
        if not slots.exists():
            messages.error(request, "🚫 Invalid slot number.")
            return redirect("booking_map")
        
        # Try to find an available slot with this number
        slot = slots.filter(is_occupied=False).first()
        if not slot:
            messages.error(request, "🚫 Selected slot is no longer available.")
            return redirect("booking_map")
    else:
        occupied = ParkingSlot.objects.filter(is_occupied=True).count()
        total = ParkingSlot.objects.count()

        if total == 0:
            messages.error(request, "🚫 No parking slots available in the system.")
            return redirect("booking_map")

        availability = predict_slot_availability(
            hour=timezone.now().hour,
            weekday=timezone.now().weekday(),
            occupied=occupied,
            total=total,
            vehicle_type=vehicle_type
        )

        if availability == 0:
            messages.error(request, "🚫 Parking is currently full. Please try again later.")
            return redirect("booking_map")

        slot = get_best_available_slot(vehicle_type)

        if not slot:
            messages.error(request, "🚫 No available parking slots for your vehicle type.")
            return redirect("booking_map")

    slot.is_occupied = True
    slot.save()

    reservation = Reservation.objects.create(
        user=request.user,
        slot_number=slot.slot_number,
        vehicle_number=vehicle_number,
        vehicle_type=vehicle_type,
        start_time=start_time,
        end_time=end_time,
        amount=float(amount),
        status="Confirmed",
        payment_status="Pending"
    )

    try:
        send_reservation_confirmation(reservation)
    except Exception as e:
        print(f"Error sending reservation email: {e}")
    
    try:
        create_reservation_notification(request.user, reservation)
    except Exception as e:
        print(f"Error creating notification: {e}")

    return redirect("payment", reservation_id=reservation.id)


# ==========================
# 💳 PAYMENT
# ==========================
@login_required
def payment(request, reservation_id):
    reservation = get_object_or_404(
        Reservation,
        id=reservation_id,
        user=request.user
    )

    if reservation.amount > 0:
        dynamic_price = reservation.amount
    else:
        base_price = 50
        demand = ParkingSlot.objects.filter(is_occupied=True).count() / max(
            1, ParkingSlot.objects.count()
        )
        dynamic_price = round(base_price * (1 + demand), 2)
        reservation.amount = dynamic_price
        reservation.save()

    if request.method == "POST":
        reservation.payment_status = "Paid"
        reservation.save()
        
        try:
            send_payment_confirmation(reservation, dynamic_price)
        except Exception as e:
            print(f"Error sending payment email: {e}")
        
        try:
            create_payment_notification(request.user, reservation, dynamic_price)
        except Exception as e:
            print(f"Error creating notification: {e}")
        
        messages.success(request, "✅ Payment successful! Your parking slot is confirmed.")
        return redirect("dashboard")

    return render(
        request,
        "parking_app/payment_legacy.html",
        {"reservation": reservation, "dynamic_price": dynamic_price}
    )


# ==========================
# 🎫 MY RESERVATIONS PAGE
# ==========================
@login_required
def my_reservations(request):
    reservations = Reservation.objects.filter(user=request.user).order_by("-reservation_time")
    
    return render(request, "parking_app/my_reservations.html", {
        "reservations": reservations,
    })


# ==========================
# 🎫 E-TICKETS
# ==========================
@login_required
def view_e_ticket(request, ticket_id):
    e_ticket = get_object_or_404(ETicket, id=ticket_id, user=request.user)
    
    is_expired = e_ticket.booking.end_time < timezone.now()
    
    return render(request, "parking_app/e_ticket_single.html", {
        "e_ticket": e_ticket,
        "booking": e_ticket.booking,
        "is_expired": is_expired,
    })


@login_required
def all_e_tickets(request):
    from django.utils import timezone
    
    tickets_with_status = []
    
    e_tickets = ETicket.objects.filter(user=request.user).order_by("-generated_at")
    for ticket in e_tickets:
        is_expired = ticket.booking.end_time < timezone.now()
        tickets_with_status.append({
            'ticket': ticket,
            'booking': ticket.booking,
            'is_expired': is_expired,
            'type': 'booking',
            'sort_date': ticket.generated_at
        })
    
    reservations = Reservation.objects.filter(
        user=request.user,
        status__in=["Confirmed", "Paid", "Checked-In", "Completed"]
    ).order_by("-reservation_time")
    
    for reservation in reservations:
        is_expired = reservation.end_time and timezone.now() > reservation.end_time
        
        ticket_number = f"RSV{reservation.id}{secrets.token_hex(2).upper()}"
        qr_data = f"reservation:{reservation.id}:{ticket_number}:{reservation.user.id}"
        qr_code = generate_qr_code_base64(qr_data)
        
        tickets_with_status.append({
            'reservation': reservation,
            'is_expired': is_expired,
            'type': 'reservation',
            'ticket_number': ticket_number,
            'qr_code': qr_code,
            'sort_date': reservation.reservation_time
        })
    
    tickets_with_status.sort(key=lambda x: x['sort_date'], reverse=True)
    
    booking_count = sum(1 for t in tickets_with_status if t['type'] == 'booking')
    reservation_count = sum(1 for t in tickets_with_status if t['type'] == 'reservation')
    
    return render(request, "parking_app/all_e_tickets.html", {
        "tickets_with_status": tickets_with_status,
        "booking_count": booking_count,
        "reservation_count": reservation_count,
    })


# ==========================
# 📊 DASHBOARD
# ==========================
@login_required
def dashboard(request):
    from django.utils import timezone
    from datetime import timedelta
    
    reservations = Reservation.objects.filter(user=request.user)
    active = reservations.filter(
        status__in=["Confirmed", "Paid"]
    ).order_by("-id").first()

    bookings = Booking.objects.filter(user=request.user).order_by("-created_at")
    pending_payments = bookings.filter(status='reserved')
    confirmed_bookings = bookings.filter(status='confirmed')
    active_bookings = bookings.filter(status='active')
    completed_bookings = bookings.filter(status='completed')
    pending_bookings = bookings.filter(status='pending')
    cancelled_bookings = bookings.filter(status='cancelled')
    
    active_booking = confirmed_bookings.first() or active_bookings.first()
    
    active_reservation = active
    if not active_reservation and active_booking:
        active_reservation = active_booking
    
    now = timezone.now()
    twenty_min_later = now + timedelta(minutes=20)
    
    checkout_reminder = None
    checked_in_res = reservations.filter(status="Checked-In").first()
    if checked_in_res and checked_in_res.end_time:
        if now < checked_in_res.end_time <= twenty_min_later:
            time_remaining = (checked_in_res.end_time - now).total_seconds() / 60
            checkout_reminder = {
                "reservation": checked_in_res,
                "minutes_remaining": int(time_remaining),
                "slot_number": checked_in_res.slot_number,
            }

    return render(
        request,
        "parking_app/dashboard.html",
        {
            "assigned_slot": active.slot_number if active else None,
            "active_reservation": active_reservation,
            "reservations": reservations.order_by("-reservation_time"),
            "balance": request.user.profile.wallet_inr,
            "total": reservations.count(),
            "confirmed": reservations.filter(status="Confirmed").count(),
            "pending": reservations.filter(status="Pending").count() + pending_bookings.count(),
            "cancelled": reservations.filter(status="Cancelled").count() + cancelled_bookings.count(),
            "completed": reservations.filter(status="Completed").count(),
            "pending_payments": pending_payments,
            "confirmed_bookings": confirmed_bookings,
            "active_bookings": active_bookings,
            "completed_bookings": completed_bookings,
            "pending_bookings": pending_bookings,
            "cancelled_bookings": cancelled_bookings,
            "new_bookings_count": bookings.count(),
            "checkout_reminder": checkout_reminder,
        }
    )


# ==========================
# 🔴🟢 LIVE SLOT STATUS
# ==========================
@login_required
def live_slot_status(request):
    my_res = Reservation.objects.filter(
        user=request.user,
        status__in=["Confirmed", "Paid"]
    ).order_by("-id").first()

    my_slot = my_res.slot_number if my_res else None

    slots = []
    for s in ParkingSlot.objects.all():
        slots.append({
            "slot_number": s.slot_number,
            "occupied": s.is_occupied,
            "is_mine": s.slot_number == my_slot,
        })

    return JsonResponse({"slots": slots})


# ==========================
# 🗺️ MAP SLOT JSON (SINGLE SOURCE)
# ==========================
def get_slots_json(request):
    return JsonResponse([
        {
            "slot_number": s.slot_number,
            "lat": s.latitude,
            "lng": s.longitude,
            "is_occupied": s.is_occupied,
        }
        for s in ParkingSlot.objects.all()
    ], safe=False)


# ==========================
# 🌍 CAMPUS MAP
# ==========================
def campus_map(request):
    return render(request, "parking_app/campus_map.html", {
        "lat": 18.5793,
        "lng": 73.8745
    })


# ==========================
# ✓ BOOKING CHECK-IN / CHECK-OUT
# ==========================
@login_required
def booking_check_in(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    
    if booking.status != 'confirmed':
        messages.error(request, "Only confirmed bookings can be checked in")
        return redirect("dashboard")
    
    if request.method == "POST":
        booking.status = 'active'
        booking.checked_in_at = timezone.now()
        booking.save()
        
        try:
            from .email_notifications import send_booking_reserved_alert
            send_booking_reserved_alert(booking)
        except Exception as e:
            print(f"Error sending check-in email: {e}")
        
        try:
            from .sms_notifications import send_booking_confirmed_sms
            send_booking_confirmed_sms(booking)
        except Exception as e:
            print(f"Error sending check-in SMS: {e}")
        
        messages.success(request, f"✅ Check-in successful! Slot {booking.slot.slot_number}")
        return redirect("dashboard")
    
    from .qr_code_utils import generate_booking_check_in_qr
    check_in_qr = generate_booking_check_in_qr(booking)
    booking.check_in_qr = check_in_qr
    booking.save()
    
    return render(request, "parking_app/booking_check_in.html", {
        "booking": booking,
        "qr_code": check_in_qr,
    })


@login_required
def booking_check_out(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    
    if booking.status != 'active':
        messages.error(request, "Booking must be active to check out")
        return redirect("dashboard")
    
    if request.method == "POST":
        booking.status = 'completed'
        booking.checked_out_at = timezone.now()
        booking.save()
        
        booking.slot.is_occupied = False
        booking.slot.save()
        
        try:
            from .email_notifications import send_booking_confirmed_alert
            send_booking_confirmed_alert(booking)
        except Exception as e:
            print(f"Error sending check-out email: {e}")
        
        try:
            from .sms_notifications import send_cancellation_confirmation_sms
            send_cancellation_confirmation_sms(booking, 0)
        except Exception as e:
            print(f"Error sending check-out SMS: {e}")
        
        messages.success(request, "✅ Check-out successful! Thank you for using Smart Parking.")
        return redirect("dashboard")
    
    from .qr_code_utils import generate_booking_check_out_qr
    check_out_qr = generate_booking_check_out_qr(booking)
    booking.check_out_qr = check_out_qr
    booking.save()
    
    return render(request, "parking_app/booking_check_out.html", {
        "booking": booking,
        "qr_code": check_out_qr,
    })


# ==========================
# ✓ CHECK-IN / CHECK-OUT
# ==========================
@login_required
def check_in(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id, user=request.user)
    
    if request.method == "POST":
        reservation.status = "Checked-In"
        reservation.checked_in_at = timezone.now()
        reservation.save()
        
        # Get or create ParkingMonitor for the reservation
        ParkingMonitor.objects.get_or_create(
            reservation=reservation,
            defaults={
                'status': 'Active',
            }
        )
        
        try:
            from .email_notifications import send_check_in_confirmation
            send_check_in_confirmation(reservation)
        except Exception as e:
            print(f"Error sending check-in email: {e}")
        
        try:
            create_check_in_notification(request.user, reservation)
        except Exception as e:
            print(f"Error creating notification: {e}")
        
        messages.success(request, f"✅ Check-in successful! Slot {reservation.slot_number}")
        return redirect("dashboard")
    
    return render(request, "parking_app/check_in.html", {"reservation": reservation})


@login_required
def check_out(request, reservation_id):
    from .email_notifications import send_check_out_receipt
    
    reservation = get_object_or_404(Reservation, id=reservation_id, user=request.user)
    
    if request.method == "POST":
        reservation.status = "Completed"
        reservation.actual_checkout_time = timezone.now()
        reservation.calculate_over_parking_charges()
        reservation.save()
        
        monitor = ParkingMonitor.objects.filter(reservation=reservation).first()
        if monitor:
            monitor.status = "Completed"
            monitor.save()
        
        slot = ParkingSlot.objects.filter(slot_number=reservation.slot_number).first()
        if slot:
            slot.is_occupied = False
            slot.save()
        
        try:
            send_check_out_receipt(reservation)
        except Exception as e:
            print(f"Error sending checkout email: {e}")
        
        try:
            total_amount = reservation.amount + reservation.over_parking_charges
            create_check_out_notification(request.user, reservation, total_amount)
        except Exception as e:
            print(f"Error creating notification: {e}")
        
        messages.success(request, "✅ Check-out successful! Thank you for using Smart Parking.")
        return redirect("dashboard")
    
    return render(request, "parking_app/check_out.html", {"reservation": reservation})


@login_required
def cancel_reservation(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id, user=request.user)
    
    if reservation.status not in ['Pending', 'Confirmed']:
        messages.error(request, "Only pending or confirmed reservations can be cancelled.")
        return redirect("dashboard")
    
    if request.method == "POST":
        reservation.status = "Cancelled"
        reservation.save()
        
        slot = ParkingSlot.objects.filter(slot_number=reservation.slot_number).first()
        if slot:
            slot.is_occupied = False
            slot.save()
        
        messages.success(request, "✅ Reservation cancelled successfully.")
        return redirect("dashboard")
    
    return redirect("dashboard")


# ==========================
# 🔔 NOTIFICATIONS
# ==========================
@login_required
def get_notifications(request):
    from .models import Notification
    
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:10]
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    
    notification_list = [
        {
            'id': n.id,
            'type': n.notification_type,
            'title': n.title,
            'message': n.message,
            'is_read': n.is_read,
            'created_at': n.created_at.isoformat(),
        }
        for n in notifications
    ]
    
    return JsonResponse({
        'notifications': notification_list,
        'unread_count': unread_count,
    })


@login_required
def mark_notification_as_read(request, notification_id):
    from .models import Notification
    
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    
    return JsonResponse({'status': 'success'})


@login_required
def notifications_page(request):
    from .models import Notification
    
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    
    return render(request, "parking_app/notifications.html", {
        'notifications': notifications,
    })


# ==========================
# 🛡️ ADMIN OVERBOOKING PREVENTION
# ==========================
@login_required
def overbooking_prevention_dashboard(request):
    if not request.user.is_staff:
        messages.error(request, "❌ Admin access only!")
        return redirect("dashboard")
    
    from .overbooking_prevention import OverbookingPreventionSystem
    
    system = OverbookingPreventionSystem()
    
    alerts = system.get_overbooking_alerts()
    stats = system.get_booking_statistics()
    capacity_threshold = system.check_capacity_threshold(0.8)
    
    occupied_slots = ParkingSlot.objects.filter(is_occupied=True).count()
    total_slots = ParkingSlot.objects.count()
    occupancy_rate = (occupied_slots / max(1, total_slots)) * 100
    
    reserved_bookings = Booking.objects.filter(status='reserved').count()
    confirmed_bookings = Booking.objects.filter(status='confirmed').count()
    active_bookings = Booking.objects.filter(status='active').count()
    
    context = {
        'alerts': alerts,
        'stats': stats,
        'capacity_threshold_reached': capacity_threshold,
        'occupied_slots': occupied_slots,
        'total_slots': total_slots,
        'occupancy_rate': round(occupancy_rate, 2),
        'reserved_count': reserved_bookings,
        'confirmed_count': confirmed_bookings,
        'active_count': active_bookings,
    }
    
    return render(request, "parking_app/admin_overbooking.html", context)


# ==========================
# 📊 ADMIN DASHBOARD
# ==========================
@login_required
def admin_dashboard(request):
    if not request.user.is_staff:
        messages.error(request, "❌ Admin access only!")
        return redirect("dashboard")
    
    total_reservations = Reservation.objects.count()
    active_reservations = Reservation.objects.filter(status__in=["Confirmed", "Checked-In"]).count()
    completed_reservations = Reservation.objects.filter(status="Completed").count()
    over_parked = Reservation.objects.filter(is_over_parked=True).count()
    
    total_slots = ParkingSlot.objects.count()
    occupied_slots = ParkingSlot.objects.filter(is_occupied=True).count()
    available_slots = total_slots - occupied_slots
    
    total_users = User.objects.count()
    total_revenue = Reservation.objects.filter(payment_status="Paid").aggregate(total=models.Sum('amount'))['total'] or 0
    
    recent_reservations = Reservation.objects.all().order_by('-created_at')[:10]
    active_monitors = ParkingMonitor.objects.filter(status="Active").select_related('reservation')
    
    context = {
        'total_reservations': total_reservations,
        'active_reservations': active_reservations,
        'completed_reservations': completed_reservations,
        'over_parked': over_parked,
        'total_slots': total_slots,
        'occupied_slots': occupied_slots,
        'available_slots': available_slots,
        'occupancy_rate': round((occupied_slots / max(1, total_slots)) * 100, 2),
        'total_users': total_users,
        'total_revenue': total_revenue,
        'recent_reservations': recent_reservations,
        'active_monitors': active_monitors,
    }
    
    return render(request, "parking_app/admin_dashboard.html", context)


# ==========================
# 📊 REPORTS & ANALYTICS
# ==========================
@login_required
def analytics(request):
    if not request.user.is_staff:
        messages.error(request, "❌ Admin access only!")
        return redirect("dashboard")
    
    from django.db.models import Count, Sum, Avg
    from django.utils.timezone import now, timedelta
    
    last_30_days = now() - timedelta(days=30)
    
    daily_reservations = Reservation.objects.filter(
        created_at__gte=last_30_days
    ).extra(
        select={'date': 'DATE(created_at)'}
    ).values('date').annotate(count=Count('id')).order_by('date')
    
    revenue_by_date = Reservation.objects.filter(
        payment_status="Paid",
        created_at__gte=last_30_days
    ).extra(
        select={'date': 'DATE(created_at)'}
    ).values('date').annotate(revenue=Sum('amount')).order_by('date')
    
    vehicle_type_dist = Reservation.objects.values('vehicle_type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    payment_status_dist = Reservation.objects.values('payment_status').annotate(
        count=Count('id')
    )
    
    status_dist = Reservation.objects.values('status').annotate(
        count=Count('id')
    )
    
    avg_parking_duration = Reservation.objects.filter(
        actual_checkout_time__isnull=False
    ).annotate(
        duration=models.F('actual_checkout_time') - models.F('start_time')
    ).aggregate(avg_duration=Avg('duration'))
    
    top_users = User.objects.annotate(
        reservation_count=Count('reservation')
    ).order_by('-reservation_count')[:5]
    
    context = {
        'daily_reservations': list(daily_reservations),
        'revenue_by_date': list(revenue_by_date),
        'vehicle_type_dist': list(vehicle_type_dist),
        'payment_status_dist': list(payment_status_dist),
        'status_dist': list(status_dist),
        'avg_parking_duration': avg_parking_duration['avg_duration'],
        'top_users': top_users,
        'last_30_days': last_30_days,
    }
    
    return render(request, "parking_app/analytics.html", context)


# ==========================
# 📍 NEAREST PARKING (PLACEHOLDER)
# ==========================
def nearest_parking(request):
    return JsonResponse({
        "status": "success",
        "message": "Nearest parking found"
    })


# ==========================
# 🔮 ADVANCED PREDICTIONS
# ==========================
def predict_availability_api(request):
    """
    API endpoint for predicting parking availability at a specific hour
    
    Query params:
    - hour: int (0-23) - Hour of the day
    - zone: str (Zone-A, Zone-B, Zone-C, Zone-D) - Parking zone
    - vehicle_type: str (Four-Wheeler, Two-Wheeler) - Vehicle type
    - priority: str (Low, Medium, High) - Priority level
    
    Returns:
    {
        'available': bool,
        'probability': float (0-1),
        'occupancy_rate': float (0-1),
        'confidence': float (0-1)
    }
    """
    try:
        hour = int(request.GET.get('hour', 12))
        zone = request.GET.get('zone')
        vehicle_type = request.GET.get('vehicle_type')
        priority = request.GET.get('priority')
        
        if hour < 0 or hour > 23:
            return JsonResponse({
                'status': 'error',
                'message': 'Hour must be between 0 and 23'
            }, status=400)
        
        prediction = get_availability_prediction(
            hour=hour,
            zone=zone,
            vehicle_type=vehicle_type,
            priority=priority
        )
        
        return JsonResponse({
            'status': 'success',
            'data': prediction
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


def forecast_24hours_api(request):
    """
    API endpoint for 24-hour parking availability forecast
    
    Query params:
    - zone: str - Parking zone (optional)
    - vehicle_type: str - Vehicle type (optional)
    - priority: str - Priority level (optional)
    
    Returns: List of hourly predictions with timestamps
    """
    try:
        zone = request.GET.get('zone')
        vehicle_type = request.GET.get('vehicle_type')
        priority = request.GET.get('priority')
        
        forecast = get_24hour_forecast(
            zone=zone,
            vehicle_type=vehicle_type,
            priority=priority
        )
        
        return JsonResponse({
            'status': 'success',
            'data': forecast
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


def parking_statistics_api(request):
    """
    API endpoint for parking zone statistics
    
    Returns occupancy statistics by zone:
    {
        'zone': {
            'avg_occupancy': float,
            'peak_occupancy': float,
            'min_occupancy': float,
            'std_dev': float
        }
    }
    """
    try:
        try:
            from .advanced_predictor import AdvancedParkingPredictor
            predictor = AdvancedParkingPredictor()
            predictor.load_models()
            stats = predictor.get_zone_statistics()
        except (ImportError, Exception):
            from .simple_predictor import get_zone_statistics
            stats = get_zone_statistics()
        
        return JsonResponse({
            'status': 'success',
            'data': stats
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@login_required
def zone_availability_dashboard(request):
    """
    Dashboard view showing all zones with availability predictions
    """
    try:
        zones = ['Zone-A', 'Zone-B', 'Zone-C', 'Zone-D']
        hours = [6, 9, 12, 15, 18, 21]
        
        zone_data = {}
        for zone in zones:
            predictions = []
            for hour in hours:
                pred = get_availability_prediction(hour=hour, zone=zone)
                predictions.append({
                    'hour': hour,
                    'time': f'{hour:02d}:00',
                    **pred
                })
            zone_data[zone] = predictions
        
        try:
            from .advanced_predictor import AdvancedParkingPredictor
            predictor = AdvancedParkingPredictor()
            predictor.load_models()
            stats = predictor.get_zone_statistics()
        except (ImportError, Exception):
            from .simple_predictor import get_zone_statistics
            stats = get_zone_statistics()
        
        context = {
            'zone_data': zone_data,
            'stats': stats,
            'zones': zones
        }
        
        return render(request, 'parking_app/zone_availability.html', context)
    except Exception as e:
        return render(request, 'parking_app/zone_availability.html', {
            'error': str(e)
        })


def all_zones_json(request):
    """
    JSON endpoint showing all zones with hourly predictions
    """
    try:
        zones = ['Zone-A', 'Zone-B', 'Zone-C', 'Zone-D']
        
        result = {}
        for zone in zones:
            zone_predictions = {}
            for hour in range(6, 22):
                pred = get_availability_prediction(hour=hour, zone=zone)
                zone_predictions[f'{hour:02d}:00'] = {
                    'available': pred['available'],
                    'probability': round(pred['probability'], 3),
                    'occupancy_rate': round(pred['occupancy_rate'], 3),
                    'confidence': round(pred['confidence'], 3)
                }
            result[zone] = zone_predictions
        
        from .advanced_predictor import AdvancedParkingPredictor
        predictor = AdvancedParkingPredictor()
        predictor.load_models()
        stats = predictor.get_zone_statistics()
        
        result['statistics'] = stats
        
        return JsonResponse({
            'status': 'success',
            'data': result
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@login_required
def parking_map_view(request):
    """
    Map view showing parking zones on Ajeenkya DY Patil University campus
    with real-time availability indicators
    """
    try:
        from datetime import datetime
        current_hour = datetime.now().hour
        
        zones_data = []
        zones = ['Zone-A', 'Zone-B', 'Zone-C', 'Zone-D']
        
        for zone in zones:
            pred = get_availability_prediction(hour=current_hour, zone=zone)
            zones_data.append({
                'name': zone,
                'available': pred['available'],
                'occupancy_rate': pred['occupancy_rate'],
                'probability': pred['probability']
            })
        
        context = {
            'zones': zones_data,
            'current_hour': current_hour
        }
        
        return render(request, 'parking_app/parking_map.html', context)
    except Exception as e:
        return render(request, 'parking_app/parking_map.html', {
            'error': str(e)
        })


def parking_map_api(request):
    """
    API endpoint for map zones with current availability
    """
    try:
        from datetime import datetime
        current_hour = datetime.now().hour
        
        zones = ['Zone-A', 'Zone-B', 'Zone-C', 'Zone-D']
        zones_data = []
        
        for zone in zones:
            pred = get_availability_prediction(hour=current_hour, zone=zone)
            zones_data.append({
                'name': zone,
                'available': pred['available'],
                'occupancy_rate': round(pred['occupancy_rate'], 2),
                'probability': round(pred['probability'], 2),
                'updated_at': datetime.now().isoformat()
            })
        
        return JsonResponse({
            'status': 'success',
            'data': zones_data,
            'current_hour': current_hour
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
