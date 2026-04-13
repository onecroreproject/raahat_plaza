"""
Models for Raahat Plaza Mall Rental Management System.
Covers: Users, Mall, Floors, Shops, RentApplications, Documents,
        Rentals, Payments, Invoices, Agreements.
"""
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import uuid


class User(AbstractUser):
    """Custom user model with role-based access."""
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('owner', 'Owner'),
        ('tenant', 'Tenant'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='tenant')
    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    is_active_account = models.BooleanField(default=True)
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    @property
    def is_admin_user(self):
        return self.role == 'admin'

    @property
    def is_owner(self):
        return self.role == 'owner'

    @property
    def is_tenant(self):
        return self.role == 'tenant'


class Mall(models.Model):
    """Mall information - only one mall (Raahat Plaza)."""
    name = models.CharField(max_length=200, default='Raahat Plaza')
    address = models.TextField(blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='mall/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'mall'

    def __str__(self):
        return self.name


class Floor(models.Model):
    """Floors in the mall."""
    mall = models.ForeignKey(Mall, on_delete=models.CASCADE, related_name='floors')
    floor_name = models.CharField(max_length=100)
    floor_order = models.IntegerField(default=0)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'floors'
        ordering = ['floor_order']

    def __str__(self):
        return f"{self.floor_name} - {self.mall.name}"

    @property
    def total_shops(self):
        return self.shops.count()

    @property
    def vacant_shops(self):
        return self.shops.filter(rental_status='vacant').count()

    @property
    def occupied_shops(self):
        return self.shops.filter(rental_status='occupied').count()


class Shop(models.Model):
    """Shops within each floor."""
    OWNERSHIP_CHOICES = (
        ('admin', 'Admin Owned'),
        ('owner', 'Owner Owned'),
    )
    RENTAL_STATUS_CHOICES = (
        ('vacant', 'Vacant'),
        ('applied', 'Application Pending'),
        ('occupied', 'Occupied'),
    )
    LISTING_CHOICES = (
        ('available', 'Available for Rent'),
        ('hidden', 'Hidden'),
    )

    floor = models.ForeignKey(Floor, on_delete=models.CASCADE, related_name='shops')
    shop_number = models.CharField(max_length=50)
    size = models.CharField(max_length=100, help_text='e.g., 500 sq ft')
    monthly_rent = models.DecimalField(max_digits=10, decimal_places=2)
    deposit_amount = models.DecimalField(max_digits=10, decimal_places=2)
    maintenance_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='shop_images/', blank=True, null=True)
    ownership_type = models.CharField(max_length=10, choices=OWNERSHIP_CHOICES, default='admin')
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                              related_name='owned_shops', limit_choices_to={'role': 'owner'})
    rental_status = models.CharField(max_length=10, choices=RENTAL_STATUS_CHOICES, default='vacant')
    listing_type = models.CharField(max_length=10, choices=LISTING_CHOICES, default='hidden')
    lease_duration = models.CharField(max_length=100, blank=True, default='12 months')
    rental_terms = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'shops'
        ordering = ['floor__floor_order', 'shop_number']
        unique_together = ['floor', 'shop_number']

    def __str__(self):
        return f"Shop {self.shop_number} - {self.floor.floor_name}"

    @property
    def is_available(self):
        return self.rental_status == 'vacant' and self.listing_type == 'available'

    @property
    def current_tenant(self):
        rental = self.rentals.filter(status='active').first()
        return rental.tenant if rental else None

    @property
    def manager(self):
        """Returns the owner, or None if admin-owned."""
        if self.ownership_type == 'owner' and self.owner:
            return self.owner
        return None


class RentApplication(models.Model):
    """Tenant rental applications."""
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('documents_pending', 'Documents Pending'),
        ('approved', 'Approved'),
        ('awaiting_payment', 'Awaiting Payment'),
        ('active', 'Active'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    )

    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='applications')
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                              related_name='received_applications')
    tenant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rent_applications')
    business_type = models.CharField(max_length=200, blank=True)
    lease_duration = models.CharField(max_length=100, blank=True)
    expected_move_in = models.DateField(null=True, blank=True)
    message = models.TextField(blank=True, help_text='Optional message to the owner/admin')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    admin_remarks = models.TextField(blank=True)
    owner_remarks = models.TextField(blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    rejected_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'rent_applications'
        ordering = ['-created_at']

    def __str__(self):
        return f"Application #{self.id} - {self.tenant.get_full_name()} for {self.shop}"

    @property
    def can_upload_documents(self):
        return self.status in ['draft', 'submitted', 'documents_pending']

    @property
    def can_make_payment(self):
        return self.status == 'awaiting_payment'

    @property
    def all_documents_approved(self):
        docs = self.documents.filter(document_type__in=['id_proof', 'address_proof', 'photo'])
        if docs.count() < 3:
            return False
        return all(doc.status == 'approved' for doc in docs)


class Document(models.Model):
    """Documents uploaded by tenants."""
    DOCUMENT_TYPE_CHOICES = (
        ('id_proof', 'ID Proof'),
        ('address_proof', 'Address Proof'),
        ('photo', 'Passport Size Photo'),
        ('business_proof', 'Business Proof'),
        ('gst_license', 'GST / Trade License'),
        ('reference', 'Supporting Reference'),
        ('agreement', 'Agreement Copy'),
        ('other', 'Other'),
    )
    STATUS_CHOICES = (
        ('uploaded', 'Uploaded'),
        ('pending_review', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('reupload_required', 'Re-upload Required'),
    )
    REQUEST_TYPE_CHOICES = (
        ('rent_application', 'Rent Application'),
        ('agreement', 'Agreement'),
        ('other', 'Other'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents')
    request_type = models.CharField(max_length=20, choices=REQUEST_TYPE_CHOICES, default='rent_application')
    request_id = models.IntegerField(null=True, blank=True, help_text='ID of the related application')
    application = models.ForeignKey(RentApplication, on_delete=models.CASCADE,
                                    related_name='documents', null=True, blank=True)
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPE_CHOICES)
    file = models.FileField(upload_to='documents/%Y/%m/')
    file_name = models.CharField(max_length=255)
    mime_type = models.CharField(max_length=100, blank=True)
    file_size = models.IntegerField(default=0, help_text='File size in bytes')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='uploaded')
    remarks = models.TextField(blank=True, help_text='Reviewer remarks')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='verified_documents')

    class Meta:
        db_table = 'documents'
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.get_document_type_display()} - {self.user.get_full_name()}"


class Rental(models.Model):
    """Active rental records."""
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('terminated', 'Terminated'),
    )

    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='rentals')
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                              related_name='owner_rentals')
    tenant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tenant_rentals')
    application = models.OneToOneField(RentApplication, on_delete=models.SET_NULL,
                                       null=True, blank=True, related_name='rental')
    rent_amount = models.DecimalField(max_digits=10, decimal_places=2)
    deposit_amount = models.DecimalField(max_digits=10, decimal_places=2)
    maintenance_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'rentals'
        ordering = ['-created_at']

    def __str__(self):
        return f"Rental: {self.tenant.get_full_name()} → {self.shop}"

    @property
    def is_active(self):
        return self.status == 'active'

    @property
    def total_monthly(self):
        return self.rent_amount + self.maintenance_amount

    @property
    def next_rent_due_date(self):
        """Calculate the next rent due date (1st of next month)."""
        import calendar
        today = timezone.now().date()
        if self.status != 'active':
            return None
        # Find the last successful payment date
        last_payment = self.payments.filter(
            status='successful', payment_type__in=['rent', 'initial']
        ).order_by('-paid_at').first()

        if last_payment and last_payment.paid_at:
            paid_date = last_payment.paid_at.date()
            # Next due is 1st of the month after the paid month
            if paid_date.month == 12:
                return paid_date.replace(year=paid_date.year + 1, month=1, day=1)
            else:
                return paid_date.replace(month=paid_date.month + 1, day=1)
        else:
            # No payment yet, due from start
            if self.start_date.month == 12:
                return self.start_date.replace(year=self.start_date.year + 1, month=1, day=1)
            else:
                return self.start_date.replace(month=self.start_date.month + 1, day=1)

    @property
    def days_until_next_rent(self):
        """Days until next rent payment is due."""
        due = self.next_rent_due_date
        if not due:
            return None
        delta = (due - timezone.now().date()).days
        return max(0, delta)

    @property
    def is_rent_overdue(self):
        """Check if rent is past due."""
        due = self.next_rent_due_date
        if not due:
            return False
        return timezone.now().date() > due

    @staticmethod
    def calculate_prorated_rent(monthly_rent, join_date):
        """Calculate pro-rated rent for partial month."""
        import calendar
        from decimal import Decimal
        days_in_month = calendar.monthrange(join_date.year, join_date.month)[1]
        remaining_days = days_in_month - join_date.day + 1  # including join day
        daily_rate = Decimal(str(monthly_rent)) / Decimal(str(days_in_month))
        return round(daily_rate * remaining_days, 2)

    @staticmethod
    def calculate_prorated_maintenance(monthly_maintenance, join_date):
        """Calculate pro-rated maintenance for partial month."""
        import calendar
        from decimal import Decimal
        days_in_month = calendar.monthrange(join_date.year, join_date.month)[1]
        remaining_days = days_in_month - join_date.day + 1
        daily_rate = Decimal(str(monthly_maintenance)) / Decimal(str(days_in_month))
        return round(daily_rate * remaining_days, 2)


class Payment(models.Model):
    """Payment records via Razorpay."""
    PAYMENT_TYPE_CHOICES = (
        ('deposit', 'Security Deposit'),
        ('rent', 'Monthly Rent'),
        ('maintenance', 'Maintenance'),
        ('initial', 'Initial Payment (Deposit + First Rent)'),
        ('penalty', 'Penalty'),
    )
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('created', 'Order Created'),
        ('successful', 'Successful'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    )

    tenant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                              related_name='received_payments')
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='payments')
    rental = models.ForeignKey(Rental, on_delete=models.SET_NULL, null=True, blank=True,
                               related_name='payments')
    application = models.ForeignKey(RentApplication, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='payments')
    payment_type = models.CharField(max_length=15, choices=PAYMENT_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=5, default='INR')
    razorpay_order_id = models.CharField(max_length=100, blank=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True)
    razorpay_signature = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    description = models.TextField(blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'payments'
        ordering = ['-created_at']

    def __str__(self):
        return f"Payment #{self.id} - ₹{self.amount} ({self.get_payment_type_display()})"


class Invoice(models.Model):
    """Generated PDF invoices."""
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, related_name='invoice')
    invoice_number = models.CharField(max_length=50, unique=True)
    pdf_path = models.FileField(upload_to='invoices/%Y/%m/', blank=True)
    tenant_name = models.CharField(max_length=200)
    shop_number = models.CharField(max_length=50)
    floor_name = models.CharField(max_length=100)
    payment_type = models.CharField(max_length=50)
    rent_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    deposit_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    maintenance_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_reference = models.CharField(max_length=100, blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'invoices'
        ordering = ['-generated_at']

    def __str__(self):
        return f"Invoice {self.invoice_number}"

    @staticmethod
    def generate_invoice_number():
        """Generate unique invoice number."""
        prefix = timezone.now().strftime('RP%Y%m')
        last = Invoice.objects.filter(
            invoice_number__startswith=prefix
        ).order_by('-invoice_number').first()
        if last:
            num = int(last.invoice_number[-4:]) + 1
        else:
            num = 1
        return f"{prefix}{num:04d}"


class Agreement(models.Model):
    """Rental agreements."""
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('uploaded', 'Uploaded'),
        ('tenant_signed', 'Tenant Signed'),
        ('owner_signed', 'Owner Signed'),
        ('verified', 'Verified'),
        ('active', 'Active'),
    )
    UPLOADED_BY_CHOICES = (
        ('admin', 'Admin'),
        ('owner', 'Owner'),
        ('tenant', 'Tenant'),
        ('system', 'System'),
    )

    rental = models.ForeignKey(Rental, on_delete=models.CASCADE, related_name='agreements')
    file = models.FileField(upload_to='agreements/%Y/%m/')
    file_name = models.CharField(max_length=255, blank=True)
    uploaded_by_role = models.CharField(max_length=10, choices=UPLOADED_BY_CHOICES, default='admin')
    uploaded_by_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='draft')
    description = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'agreements'
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"Agreement for Rental #{self.rental.id}"


class Notification(models.Model):
    """System notifications."""
    TYPE_CHOICES = (
        ('info', 'Information'),
        ('success', 'Success'),
        ('warning', 'Warning'),
        ('error', 'Error'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='info')
    is_read = models.BooleanField(default=False)
    link = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} → {self.user.username}"
