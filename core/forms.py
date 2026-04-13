"""
Forms for Raahat Plaza Mall Rental Management System.
"""
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import (
    User, Mall, Floor, Shop, RentApplication, Document,
    Rental, Agreement
)


# ─── Authentication Forms ──────────────────────────────────────

class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-input', 'placeholder': 'Username', 'id': 'login-username',
            'autocomplete': 'username'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input', 'placeholder': 'Password', 'id': 'login-password',
            'autocomplete': 'current-password'
        })
    )


class TenantRegistrationForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'First Name', 'id': 'reg-first-name'})
    )
    last_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Last Name', 'id': 'reg-last-name'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'Email', 'id': 'reg-email'})
    )
    phone = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Phone Number', 'id': 'reg-phone'})
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Password', 'id': 'reg-password1'})
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Confirm Password', 'id': 'reg-password2'})
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'phone', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Username', 'id': 'reg-username'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'tenant'
        if commit:
            user.save()
        return user


# ─── Admin Panel Forms ──────────────────────────────────────────

class MallForm(forms.ModelForm):
    class Meta:
        model = Mall
        fields = ['name', 'address', 'description', 'image']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'id': 'mall-name'}),
            'address': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'id': 'mall-address'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 4, 'id': 'mall-description'}),
            'image': forms.FileInput(attrs={'class': 'form-input', 'id': 'mall-image'}),
        }


class FloorForm(forms.ModelForm):
    class Meta:
        model = Floor
        fields = ['floor_name', 'floor_order', 'description']
        widgets = {
            'floor_name': forms.TextInput(attrs={'class': 'form-input', 'id': 'floor-name'}),
            'floor_order': forms.NumberInput(attrs={'class': 'form-input', 'id': 'floor-order'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'id': 'floor-description'}),
        }


class ShopForm(forms.ModelForm):
    class Meta:
        model = Shop
        fields = [
            'floor', 'shop_number', 'size', 'monthly_rent', 'deposit_amount',
            'maintenance_charge', 'description', 'image', 'ownership_type',
            'owner', 'rental_status', 'listing_type', 'lease_duration', 'rental_terms'
        ]
        widgets = {
            'floor': forms.Select(attrs={'class': 'form-input', 'id': 'shop-floor'}),
            'shop_number': forms.TextInput(attrs={'class': 'form-input', 'id': 'shop-number'}),
            'size': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g., 500 sq ft', 'id': 'shop-size'}),
            'monthly_rent': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01', 'id': 'shop-rent'}),
            'deposit_amount': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01', 'id': 'shop-deposit'}),
            'maintenance_charge': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01', 'id': 'shop-maintenance'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'id': 'shop-description'}),
            'image': forms.FileInput(attrs={'class': 'form-input', 'id': 'shop-image'}),
            'ownership_type': forms.Select(attrs={'class': 'form-input', 'id': 'shop-ownership'}),
            'owner': forms.Select(attrs={'class': 'form-input', 'id': 'shop-owner'}),
            'rental_status': forms.Select(attrs={'class': 'form-input', 'id': 'shop-rental-status'}),
            'listing_type': forms.Select(attrs={'class': 'form-input', 'id': 'shop-listing-type'}),
            'lease_duration': forms.TextInput(attrs={'class': 'form-input', 'id': 'shop-lease-duration'}),
            'rental_terms': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'id': 'shop-rental-terms'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['owner'].queryset = User.objects.filter(role='owner', is_active=True)
        self.fields['owner'].required = False


class OwnerCreateForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'First Name'})
    )
    last_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Last Name'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'Email'})
    )
    phone = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Phone Number'})
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Password'})
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Confirm Password'})
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'phone', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Username'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'owner'
        if commit:
            user.save()
        return user


class OwnerEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'is_active_account']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-input'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input'}),
            'email': forms.EmailInput(attrs={'class': 'form-input'}),
            'phone': forms.TextInput(attrs={'class': 'form-input'}),
            'is_active_account': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }


class TenantEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'is_active_account']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-input'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input'}),
            'email': forms.EmailInput(attrs={'class': 'form-input'}),
            'phone': forms.TextInput(attrs={'class': 'form-input'}),
            'is_active_account': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }


# ─── Rental Application Forms ──────────────────────────────────

class RentApplicationForm(forms.ModelForm):
    class Meta:
        model = RentApplication
        fields = ['business_type', 'lease_duration', 'expected_move_in', 'message']
        widgets = {
            'business_type': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g., Clothing Store, Restaurant', 'id': 'app-business'}),
            'lease_duration': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g., 12 months', 'id': 'app-lease'}),
            'expected_move_in': forms.DateInput(attrs={'class': 'form-input', 'type': 'date', 'id': 'app-movein'}),
            'message': forms.Textarea(attrs={'class': 'form-input', 'rows': 4, 'placeholder': 'Optional message to the owner/admin', 'id': 'app-message'}),
        }


class DocumentUploadForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['document_type', 'file']
        widgets = {
            'document_type': forms.Select(attrs={'class': 'form-input', 'id': 'doc-type'}),
            'file': forms.FileInput(attrs={'class': 'form-input', 'accept': '.pdf,.jpg,.jpeg,.png', 'id': 'doc-file'}),
        }

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            if file.size > 5 * 1024 * 1024:
                raise forms.ValidationError('File size must be under 5MB.')
            allowed_types = ['application/pdf', 'image/jpeg', 'image/jpg', 'image/png']
            if file.content_type not in allowed_types:
                raise forms.ValidationError('Only PDF, JPG, JPEG, and PNG files are allowed.')
        return file


class DocumentReviewForm(forms.Form):
    status = forms.ChoiceField(
        choices=[
            ('approved', 'Approve'),
            ('rejected', 'Reject'),
            ('reupload_required', 'Re-upload Required'),
        ],
        widget=forms.Select(attrs={'class': 'form-input', 'id': 'review-status'})
    )
    remarks = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'Add remarks...', 'id': 'review-remarks'})
    )


class ApplicationReviewForm(forms.Form):
    action = forms.ChoiceField(
        choices=[
            ('approve', 'Approve Application'),
            ('reject', 'Reject Application'),
            ('request_docs', 'Request Document Re-upload'),
        ],
        widget=forms.Select(attrs={'class': 'form-input', 'id': 'app-review-action'})
    )
    remarks = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'Add remarks...', 'id': 'app-review-remarks'})
    )


# ─── Owner Panel Forms ──────────────────────────────────────────

class ShopRentalUpdateForm(forms.ModelForm):
    """Form for owner to update rental details of their shop."""
    class Meta:
        model = Shop
        fields = [
            'monthly_rent', 'deposit_amount', 'maintenance_charge',
            'lease_duration', 'description', 'rental_terms', 'listing_type'
        ]
        widgets = {
            'monthly_rent': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'deposit_amount': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'maintenance_charge': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'lease_duration': forms.TextInput(attrs={'class': 'form-input'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'rental_terms': forms.Textarea(attrs={'class': 'form-input', 'rows': 4}),
            'listing_type': forms.Select(attrs={'class': 'form-input'}),
        }


# ─── Agreement Forms ────────────────────────────────────────────

class AgreementUploadForm(forms.ModelForm):
    class Meta:
        model = Agreement
        fields = ['file', 'description']
        widgets = {
            'file': forms.FileInput(attrs={'class': 'form-input', 'accept': '.pdf', 'id': 'agreement-file'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'id': 'agreement-desc'}),
        }
