"""
Management command to set up initial data for Raahat Plaza.
Creates the mall, floors, sample shops, and admin account.
"""
from django.core.management.base import BaseCommand
from core.models import User, Mall, Floor, Shop


class Command(BaseCommand):
    help = 'Set up initial data for Raahat Plaza'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Setting up Raahat Plaza...'))

        # Create Admin User
        if not User.objects.filter(username='admin').exists():
            admin = User.objects.create_superuser(
                username='admin',
                email='admin@raahatplaza.com',
                password='admin123',
                first_name='Admin',
                last_name='Plaza',
                role='admin',
                phone='9999999999',
            )
            self.stdout.write(self.style.SUCCESS(f'Admin user created: admin / admin123'))
        else:
            admin = User.objects.get(username='admin')
            self.stdout.write(self.style.WARNING('Admin user already exists'))

        # Create Mall
        mall, created = Mall.objects.get_or_create(
            id=1,
            defaults={
                'name': 'Raahat Plaza',
                'address': 'Main Road, City Center',
                'description': 'Raahat Plaza is a premium commercial complex offering retail and office spaces across 5 floors. Strategically located at the city center with ample parking and modern amenities.',
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Mall "Raahat Plaza" created'))
        else:
            self.stdout.write(self.style.WARNING('Mall already exists'))

        # Create Floors
        floors_data = [
            {'floor_name': 'Basement', 'floor_order': 0, 'description': 'Underground level with storage and utility shops'},
            {'floor_name': 'Ground Floor', 'floor_order': 1, 'description': 'Main entrance level with high-visibility retail shops'},
            {'floor_name': '1st Floor', 'floor_order': 2, 'description': 'First floor with boutique and fashion retail spaces'},
            {'floor_name': '2nd Floor', 'floor_order': 3, 'description': 'Second floor with electronics and specialty shops'},
            {'floor_name': '3rd Floor', 'floor_order': 4, 'description': 'Top floor with restaurants and entertainment'},
        ]

        for fdata in floors_data:
            floor, created = Floor.objects.get_or_create(
                mall=mall,
                floor_name=fdata['floor_name'],
                defaults=fdata
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'  Floor "{floor.floor_name}" created'))

        # Create Sample Shops
        sample_shops = [
            # Basement
            {'floor': 'Basement', 'shop_number': 'B-01', 'size': '300 sq ft', 'monthly_rent': 15000, 'deposit_amount': 45000, 'maintenance_charge': 2000, 'description': 'Compact basement shop ideal for storage or small retail'},
            {'floor': 'Basement', 'shop_number': 'B-02', 'size': '350 sq ft', 'monthly_rent': 18000, 'deposit_amount': 54000, 'maintenance_charge': 2000, 'description': 'Well-ventilated basement shop with separate entrance'},
            {'floor': 'Basement', 'shop_number': 'B-03', 'size': '400 sq ft', 'monthly_rent': 20000, 'deposit_amount': 60000, 'maintenance_charge': 2500, 'description': 'Spacious basement unit for wholesale or storage business'},
            # Ground Floor
            {'floor': 'Ground Floor', 'shop_number': 'G-01', 'size': '500 sq ft', 'monthly_rent': 35000, 'deposit_amount': 105000, 'maintenance_charge': 3000, 'description': 'Prime ground floor shop with direct road-facing entrance'},
            {'floor': 'Ground Floor', 'shop_number': 'G-02', 'size': '450 sq ft', 'monthly_rent': 32000, 'deposit_amount': 96000, 'maintenance_charge': 3000, 'description': 'Corner shop with excellent foot traffic and visibility'},
            {'floor': 'Ground Floor', 'shop_number': 'G-03', 'size': '600 sq ft', 'monthly_rent': 40000, 'deposit_amount': 120000, 'maintenance_charge': 3500, 'description': 'Large ground floor showroom with glass frontage'},
            {'floor': 'Ground Floor', 'shop_number': 'G-04', 'size': '400 sq ft', 'monthly_rent': 30000, 'deposit_amount': 90000, 'maintenance_charge': 2500, 'description': 'Centrally located shop near main entrance'},
            # 1st Floor
            {'floor': '1st Floor', 'shop_number': 'F1-01', 'size': '450 sq ft', 'monthly_rent': 25000, 'deposit_amount': 75000, 'maintenance_charge': 2500, 'description': 'Modern first floor shop with escalator access'},
            {'floor': '1st Floor', 'shop_number': 'F1-02', 'size': '500 sq ft', 'monthly_rent': 28000, 'deposit_amount': 84000, 'maintenance_charge': 2500, 'description': 'Spacious shop ideal for clothing or fashion retail'},
            {'floor': '1st Floor', 'shop_number': 'F1-03', 'size': '400 sq ft', 'monthly_rent': 22000, 'deposit_amount': 66000, 'maintenance_charge': 2000, 'description': 'Cozy shop with premium interiors'},
            # 2nd Floor
            {'floor': '2nd Floor', 'shop_number': 'F2-01', 'size': '500 sq ft', 'monthly_rent': 22000, 'deposit_amount': 66000, 'maintenance_charge': 2500, 'description': 'Second floor shop perfect for electronics or tech'},
            {'floor': '2nd Floor', 'shop_number': 'F2-02', 'size': '450 sq ft', 'monthly_rent': 20000, 'deposit_amount': 60000, 'maintenance_charge': 2000, 'description': 'Well-lit shop with modern amenities'},
            {'floor': '2nd Floor', 'shop_number': 'F2-03', 'size': '550 sq ft', 'monthly_rent': 25000, 'deposit_amount': 75000, 'maintenance_charge': 2500, 'description': 'Large shop suitable for showroom or office'},
            # 3rd Floor
            {'floor': '3rd Floor', 'shop_number': 'F3-01', 'size': '600 sq ft', 'monthly_rent': 20000, 'deposit_amount': 60000, 'maintenance_charge': 3000, 'description': 'Top floor space ideal for restaurant or cafe'},
            {'floor': '3rd Floor', 'shop_number': 'F3-02', 'size': '800 sq ft', 'monthly_rent': 30000, 'deposit_amount': 90000, 'maintenance_charge': 3500, 'description': 'Premium large space for entertainment or dining'},
            {'floor': '3rd Floor', 'shop_number': 'F3-03', 'size': '500 sq ft', 'monthly_rent': 18000, 'deposit_amount': 54000, 'maintenance_charge': 2500, 'description': 'Top floor shop with terrace access'},
        ]

        for sdata in sample_shops:
            floor = Floor.objects.get(floor_name=sdata['floor'], mall=mall)
            shop, created = Shop.objects.get_or_create(
                floor=floor,
                shop_number=sdata['shop_number'],
                defaults={
                    'size': sdata['size'],
                    'monthly_rent': sdata['monthly_rent'],
                    'deposit_amount': sdata['deposit_amount'],
                    'maintenance_charge': sdata['maintenance_charge'],
                    'description': sdata['description'],
                    'ownership_type': 'admin',
                    'rental_status': 'vacant',
                    'listing_type': 'available',
                    'lease_duration': '12 months',
                }
            )
            if created:
                self.stdout.write(f'    Shop {shop.shop_number} created')

        # Create a sample owner
        if not User.objects.filter(username='owner1').exists():
            owner = User.objects.create_user(
                username='owner1',
                email='owner1@raahatplaza.com',
                password='owner123',
                first_name='Rahul',
                last_name='Sharma',
                role='owner',
                phone='9876543210',
            )
            # Assign some shops to owner
            shops_to_assign = Shop.objects.filter(shop_number__in=['G-01', 'G-02', 'F1-01'])
            for shop in shops_to_assign:
                shop.owner = owner
                shop.ownership_type = 'owner'
                shop.save()
            self.stdout.write(self.style.SUCCESS(f'Owner created: owner1 / owner123 (3 shops assigned)'))

        # Create a sample tenant
        if not User.objects.filter(username='tenant1').exists():
            User.objects.create_user(
                username='tenant1',
                email='tenant1@raahatplaza.com',
                password='tenant123',
                first_name='Priya',
                last_name='Patel',
                role='tenant',
                phone='9876543211',
            )
            self.stdout.write(self.style.SUCCESS(f'Tenant created: tenant1 / tenant123'))

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write(self.style.SUCCESS('Raahat Plaza setup complete!'))
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write('')
        self.stdout.write('Login credentials:')
        self.stdout.write(f'  Admin:  admin / admin123')
        self.stdout.write(f'  Owner:  owner1 / owner123')
        self.stdout.write(f'  Tenant: tenant1 / tenant123')
        self.stdout.write('')
        self.stdout.write('Run: python manage.py runserver')
        self.stdout.write('')
