# Raahat Plaza - Mall Rental Management System

A comprehensive Mall Rental Management Platform built with Django, featuring role-based access for **Admin**, **Owner**, and **Tenant** users. Manages the complete lifecycle of shop rentals including applications, document verification, Razorpay payments, PDF invoice generation, and agreement management.

## Features

- **Mall Management** - Create and manage mall structure (floors, shops)
- **Role-Based Dashboards** - Separate panels for Admin, Owner, and Tenant
- **Shop Management** - Create, assign, and list shops for rent
- **Rental Applications** - Full application workflow with status tracking
- **Document Management** - Upload, review, approve/reject documents
- **Razorpay Payments** - Secure payment integration for deposits and rent
- **PDF Invoices** - Auto-generated invoices using ReportLab
- **Agreement Management** - Upload and manage rental agreements
- **Email Notifications** - SMTP-based email alerts
- **In-App Notifications** - Real-time notification system
- **Reports & Analytics** - Admin reports with floor-wise metrics

## Tech Stack

- **Backend**: Django 4.2+
- **Database**: SQLite3
- **Frontend**: HTML, CSS, JavaScript
- **Payment**: Razorpay
- **PDF Generation**: ReportLab
- **Email**: SMTP (Gmail)

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Edit the `.env` file with your actual credentials:

```
RAZORPAY_KEY_ID=rzp_test_XXXXXXXXXXXX
RAZORPAY_KEY_SECRET=XXXXXXXXXXXXXXXXXXXXXXXX
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### 3. Run Migrations

```bash
python manage.py makemigrations core
python manage.py migrate
```

### 4. Setup Initial Data

```bash
python manage.py setup_raahat_plaza
```

This creates:
- Mall structure (5 floors, 16 shops)
- Admin account: `admin` / `admin123`
- Sample Owner: `owner1` / `owner123`
- Sample Tenant: `tenant1` / `tenant123`

### 5. Run the Server

```bash
python manage.py runserver
```

Visit: **http://127.0.0.1:8000/**

## Login Credentials

| Role   | Username | Password   |
|--------|----------|------------|
| Admin  | admin    | admin123   |
| Owner  | owner1   | owner123   |
| Tenant | tenant1  | tenant123  |

## Project Structure

```
Raahat_Plaza/
├── manage.py
├── requirements.txt
├── .env
├── raahat_plaza/              # Django project settings
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── core/                      # Main Django app
│   ├── models.py              # All database models
│   ├── forms.py               # All forms
│   ├── admin.py               # Django admin config
│   ├── urls.py                # URL routing
│   ├── decorators.py          # Role-based access decorators
│   ├── utils.py               # Razorpay, PDF, Email utilities
│   ├── context_processors.py  # Global template context
│   ├── views/
│   │   ├── auth_views.py      # Login, register, dashboards
│   │   ├── admin_views.py     # Admin panel views
│   │   ├── owner_views.py     # Owner panel views
│   │   ├── tenant_views.py    # Tenant panel views
│   │   └── payment_views.py   # Razorpay payment views
│   ├── templatetags/
│   │   └── custom_filters.py  # Currency, badge filters
│   └── management/
│       └── commands/
│           └── setup_raahat_plaza.py
├── templates/                 # All HTML templates
│   ├── base.html
│   ├── base_dashboard.html
│   ├── base_public.html
│   ├── auth/
│   ├── public/
│   ├── admin_panel/
│   ├── owner_panel/
│   ├── tenant_panel/
│   └── includes/
├── static/
│   ├── css/style.css
│   └── js/main.js
└── media/                     # Uploaded files
```

## Complete Workflow

1. **Admin** creates Raahat Plaza, floors, and shops
2. **Admin** assigns shops to owners
3. **Owner** logs in and lists shops for rent
4. **Tenant** registers and applies for rent
5. **Tenant** uploads documents (ID proof, address proof, photo)
6. **Owner/Admin** reviews and approves documents
7. **Owner/Admin** approves the application
8. **Tenant** makes Razorpay payment (deposit + first rent + maintenance)
9. Payment is verified → Rental is confirmed
10. Agreement is uploaded/generated
11. Invoice is generated (PDF)
12. Email notification is sent
13. Tenant continues monthly rent payments through the system
