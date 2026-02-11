from django.core.management.base import BaseCommand
from books.models import Business, Category, PaymentMode, Party
from users.models import CustomUser

class Command(BaseCommand):
    help = 'Populate initial data for categories and payment modes'

    def handle(self, *args, **kwargs):
        self.stdout.write('Starting to populate initial data...')
        
        # Get the first user's first business (or create one)
        try:
            user = CustomUser.objects.first()
            if not user:
                self.stdout.write(self.style.ERROR('No users found. Please create a user first.'))
                return
            
            business = Business.objects.filter(owner=user).first()
            if not business:
                business = Business.objects.create(
                    owner=user,
                    name=f"{user.full_name}'s Business",
                    description='Default business'
                )
                self.stdout.write(self.style.SUCCESS(f'Created business: {business.name}'))
            else:
                self.stdout.write(f'Using existing business: {business.name}')
            
            # Create default categories
            categories = [
                'Sales',
                'Purchase',
                'Salary',
                'Rent',
                'Utilities',
                'Transport',
                'Office Supplies',
                'Marketing',
                'Maintenance',
                'Other Income',
                'Other Expense',
            ]
            
            created_categories = 0
            for name in categories:
                category, created = Category.objects.get_or_create(
                    business=business,
                    name=name
                )
                if created:
                    created_categories += 1
                    self.stdout.write(f'  + Created category: {name}')
            
            self.stdout.write(self.style.SUCCESS(f'Categories: {created_categories} created, {len(categories) - created_categories} already existed'))
            
            # Create default payment modes
            payment_modes = [
                'Cash',
                'Bank Transfer',
                'UPI',
                'Credit Card',
                'Debit Card',
                'Cheque',
                'Mobile Wallet',
            ]
            
            created_modes = 0
            for name in payment_modes:
                mode, created = PaymentMode.objects.get_or_create(
                    business=business,
                    name=name
                )
                if created:
                    created_modes += 1
                    self.stdout.write(f'  + Created payment mode: {name}')
            
            self.stdout.write(self.style.SUCCESS(f'Payment Modes: {created_modes} created, {len(payment_modes) - created_modes} already existed'))
            
            # Create some default parties (optional)
            parties = [
                ('General Customer', '9999999999'),
                ('General Supplier', '8888888888'),
            ]
            
            created_parties = 0
            for name, phone in parties:
                party, created = Party.objects.get_or_create(
                    business=business,
                    name=name,
                    defaults={'phone': phone}
                )
                if created:
                    created_parties += 1
                    self.stdout.write(f'  + Created party: {name}')
            
            self.stdout.write(self.style.SUCCESS(f'Parties: {created_parties} created, {len(parties) - created_parties} already existed'))
            
            self.stdout.write(self.style.SUCCESS('\n✅ Initial data population completed successfully!'))
            self.stdout.write(f'Business: {business.name}')
            self.stdout.write(f'Total Categories: {Category.objects.filter(business=business).count()}')
            self.stdout.write(f'Total Payment Modes: {PaymentMode.objects.filter(business=business).count()}')
            self.stdout.write(f'Total Parties: {Party.objects.filter(business=business).count()}')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
