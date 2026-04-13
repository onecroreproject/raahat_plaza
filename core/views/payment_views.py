"""
Payment views: Razorpay order creation, payment verification,
rental confirmation, invoice generation.
"""
import json
from decimal import Decimal
from datetime import timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.conf import settings

from ..models import (
    Shop, RentApplication, Rental, Payment, Invoice
)
from ..decorators import tenant_required
from ..utils import (
    create_razorpay_order, verify_razorpay_payment,
    generate_invoice_pdf, send_payment_confirmation_email,
    create_notification
)


@tenant_required
def initiate_payment(request, application_id):
    """Tenant initiates Razorpay payment for approved application."""
    application = get_object_or_404(
        RentApplication.objects.select_related('shop', 'shop__floor', 'owner'),
        pk=application_id, tenant=request.user
    )

    if application.status != 'awaiting_payment':
        messages.error(request, 'Payment is not available for this application.')
        return redirect('tenant_application_detail', pk=application.id)

    shop = application.shop
    today = timezone.now().date()

    # Calculate pro-rated rent for remaining days in current month
    import calendar
    days_in_month = calendar.monthrange(today.year, today.month)[1]
    remaining_days = days_in_month - today.day + 1  # including today

    deposit = shop.deposit_amount
    # Pro-rated first month rent
    prorated_rent = Rental.calculate_prorated_rent(shop.monthly_rent, today)
    prorated_maintenance = Rental.calculate_prorated_maintenance(shop.maintenance_charge, today)
    total = deposit + prorated_rent + prorated_maintenance

    if request.method == 'POST':
        try:
            # Create Razorpay order
            order = create_razorpay_order(
                amount=total,
                currency='INR',
                receipt=f'app_{application.id}',
                notes={
                    'application_id': application.id,
                    'tenant': request.user.get_full_name(),
                    'shop': shop.shop_number,
                }
            )

            # Create payment record
            payment = Payment.objects.create(
                tenant=request.user,
                owner=shop.owner,
                shop=shop,
                application=application,
                payment_type='initial',
                amount=total,
                razorpay_order_id=order['id'],
                status='created',
                description=f'Initial payment for Shop {shop.shop_number} (Deposit ₹{deposit} + Pro-rated Rent ₹{prorated_rent} for {remaining_days} days + Maintenance ₹{prorated_maintenance})',
            )

            context = {
                'application': application,
                'shop': shop,
                'payment': payment,
                'order': order,
                'razorpay_key': settings.RAZORPAY_KEY_ID,
                'amount': int(total * 100),
                'amount_display': total,
                'deposit': deposit,
                'rent': prorated_rent,
                'maintenance': prorated_maintenance,
                'remaining_days': remaining_days,
                'days_in_month': days_in_month,
                'full_rent': shop.monthly_rent,
                'full_maintenance': shop.maintenance_charge,
                'user': request.user,
            }
            return render(request, 'tenant_panel/payment_checkout.html', context)

        except Exception as e:
            messages.error(request, f'Error creating payment order: {str(e)}')
            return redirect('tenant_application_detail', pk=application.id)

    context = {
        'application': application,
        'shop': shop,
        'deposit': deposit,
        'rent': prorated_rent,
        'maintenance': prorated_maintenance,
        'total': total,
        'remaining_days': remaining_days,
        'days_in_month': days_in_month,
        'full_rent': shop.monthly_rent,
        'full_maintenance': shop.maintenance_charge,
        'join_date': today,
    }
    return render(request, 'tenant_panel/payment_summary.html', context)


@csrf_exempt
@login_required
def verify_payment(request):
    """Verify Razorpay payment after completion."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request'}, status=400)

    try:
        data = json.loads(request.body)
        razorpay_order_id = data.get('razorpay_order_id')
        razorpay_payment_id = data.get('razorpay_payment_id')
        razorpay_signature = data.get('razorpay_signature')

        if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
            return JsonResponse({'error': 'Missing payment details'}, status=400)

        # Get payment record
        payment = Payment.objects.get(razorpay_order_id=razorpay_order_id)

        # Verify signature
        is_valid = verify_razorpay_payment(
            razorpay_order_id, razorpay_payment_id, razorpay_signature
        )

        if is_valid:
            # Update payment
            payment.razorpay_payment_id = razorpay_payment_id
            payment.razorpay_signature = razorpay_signature
            payment.status = 'successful'
            payment.paid_at = timezone.now()
            payment.save()

            # Create rental record
            application = payment.application
            shop = payment.shop

            # Calculate lease end date
            lease_months = 12  # default
            try:
                lease_text = application.lease_duration if application else shop.lease_duration
                lease_months = int(''.join(filter(str.isdigit, lease_text)) or '12')
            except (ValueError, AttributeError):
                lease_months = 12

            rental = Rental.objects.create(
                shop=shop,
                owner=shop.owner,
                tenant=payment.tenant,
                application=application,
                rent_amount=shop.monthly_rent,
                deposit_amount=shop.deposit_amount,
                maintenance_amount=shop.maintenance_charge,
                start_date=timezone.now().date(),
                end_date=timezone.now().date() + timedelta(days=lease_months * 30),
                status='active',
            )

            # Link payment to rental
            payment.rental = rental
            payment.save()

            # Update shop status
            shop.rental_status = 'occupied'
            shop.listing_type = 'hidden'
            shop.save()

            # Update application status
            if application:
                application.status = 'active'
                application.save()

            # Generate invoice
            invoice = Invoice.objects.create(
                payment=payment,
                invoice_number=Invoice.generate_invoice_number(),
                tenant_name=payment.tenant.get_full_name(),
                shop_number=shop.shop_number,
                floor_name=shop.floor.floor_name,
                payment_type=payment.get_payment_type_display(),
                rent_amount=shop.monthly_rent,
                deposit_amount=shop.deposit_amount,
                maintenance_amount=shop.maintenance_charge,
                total_amount=payment.amount,
                payment_reference=razorpay_payment_id,
            )

            # Generate PDF
            try:
                generate_invoice_pdf(invoice)
            except Exception as e:
                print(f"PDF generation error: {e}")

            # Send email
            send_payment_confirmation_email(payment, invoice)

            # Notifications
            create_notification(
                payment.tenant,
                'Payment Successful',
                f'Your payment of ₹{payment.amount} for Shop {shop.shop_number} was successful.',
                'success',
                f'/tenant/rental/{rental.id}/'
            )

            if shop.owner:
                create_notification(
                    shop.owner,
                    'New Tenant Payment',
                    f'{payment.tenant.get_full_name()} paid ₹{payment.amount} for Shop {shop.shop_number}.',
                    'success',
                    f'/owner/shop/{shop.id}/'
                )

            return JsonResponse({
                'status': 'success',
                'message': 'Payment verified successfully',
                'rental_id': rental.id,
                'invoice_number': invoice.invoice_number,
            })
        else:
            payment.status = 'failed'
            payment.save()
            return JsonResponse({
                'status': 'failed',
                'message': 'Payment verification failed'
            }, status=400)

    except Payment.DoesNotExist:
        return JsonResponse({'error': 'Payment not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@tenant_required
def payment_success(request):
    """Payment success page."""
    rental_id = request.GET.get('rental_id')
    invoice_number = request.GET.get('invoice')
    rental = None
    invoice = None

    if rental_id:
        rental = Rental.objects.filter(id=rental_id, tenant=request.user).first()
    if invoice_number:
        invoice = Invoice.objects.filter(invoice_number=invoice_number).first()

    context = {'rental': rental, 'invoice': invoice}
    return render(request, 'tenant_panel/payment_success.html', context)


@tenant_required
def pay_monthly_rent(request, rental_id):
    """Tenant pays monthly rent."""
    rental = get_object_or_404(Rental, pk=rental_id, tenant=request.user, status='active')
    shop = rental.shop
    total = rental.rent_amount + rental.maintenance_amount

    if request.method == 'POST':
        try:
            order = create_razorpay_order(
                amount=total,
                currency='INR',
                receipt=f'rent_{rental.id}_{timezone.now().strftime("%Y%m")}',
                notes={
                    'rental_id': rental.id,
                    'tenant': request.user.get_full_name(),
                    'shop': shop.shop_number,
                    'type': 'monthly_rent',
                }
            )

            payment = Payment.objects.create(
                tenant=request.user,
                owner=rental.owner,
                shop=shop,
                rental=rental,
                payment_type='rent',
                amount=total,
                razorpay_order_id=order['id'],
                status='created',
                description=f'Monthly rent for Shop {shop.shop_number} - {timezone.now().strftime("%B %Y")}',
            )

            context = {
                'rental': rental,
                'shop': shop,
                'payment': payment,
                'order': order,
                'razorpay_key': settings.RAZORPAY_KEY_ID,
                'amount': int(total * 100),
                'amount_display': total,
                'rent': rental.rent_amount,
                'maintenance': rental.maintenance_amount,
                'user': request.user,
                'is_monthly': True,
            }
            return render(request, 'tenant_panel/payment_checkout.html', context)

        except Exception as e:
            messages.error(request, f'Error creating payment order: {str(e)}')
            return redirect('tenant_rental_detail', pk=rental_id)

    context = {
        'rental': rental,
        'shop': shop,
        'rent': rental.rent_amount,
        'maintenance': rental.maintenance_amount,
        'total': total,
    }
    return render(request, 'tenant_panel/monthly_payment_summary.html', context)


@csrf_exempt
@login_required
def verify_monthly_payment(request):
    """Verify monthly rent payment."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request'}, status=400)

    try:
        data = json.loads(request.body)
        razorpay_order_id = data.get('razorpay_order_id')
        razorpay_payment_id = data.get('razorpay_payment_id')
        razorpay_signature = data.get('razorpay_signature')

        payment = Payment.objects.get(razorpay_order_id=razorpay_order_id)

        is_valid = verify_razorpay_payment(
            razorpay_order_id, razorpay_payment_id, razorpay_signature
        )

        if is_valid:
            payment.razorpay_payment_id = razorpay_payment_id
            payment.razorpay_signature = razorpay_signature
            payment.status = 'successful'
            payment.paid_at = timezone.now()
            payment.save()

            # Generate invoice
            invoice = Invoice.objects.create(
                payment=payment,
                invoice_number=Invoice.generate_invoice_number(),
                tenant_name=payment.tenant.get_full_name(),
                shop_number=payment.shop.shop_number,
                floor_name=payment.shop.floor.floor_name,
                payment_type=payment.get_payment_type_display(),
                rent_amount=payment.rental.rent_amount if payment.rental else 0,
                deposit_amount=0,
                maintenance_amount=payment.rental.maintenance_amount if payment.rental else 0,
                total_amount=payment.amount,
                payment_reference=razorpay_payment_id,
            )

            try:
                generate_invoice_pdf(invoice)
            except Exception as e:
                print(f"PDF generation error: {e}")

            send_payment_confirmation_email(payment, invoice)

            create_notification(
                payment.tenant,
                'Rent Payment Successful',
                f'Monthly rent of ₹{payment.amount} for Shop {payment.shop.shop_number} paid successfully.',
                'success',
            )

            return JsonResponse({
                'status': 'success',
                'message': 'Payment verified successfully',
                'invoice_number': invoice.invoice_number,
            })
        else:
            payment.status = 'failed'
            payment.save()
            return JsonResponse({
                'status': 'failed',
                'message': 'Payment verification failed'
            }, status=400)

    except Payment.DoesNotExist:
        return JsonResponse({'error': 'Payment not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
