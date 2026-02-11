from django.db import models
from django.conf import settings
import uuid

class Business(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='businesses')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Cashbook(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='cashbooks')
    name = models.CharField(max_length=255)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.business.name})"

class Member(models.Model):
    ROLE_CHOICES = [
        ('ADMIN', 'Admin'),
        ('EDITOR', 'Editor'),
        ('VIEWER', 'Viewer'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='memberships')
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='members')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='VIEWER')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'business')

    def __str__(self):
        return f"{self.user.username} - {self.role}"

class Category(models.Model):
    TYPE_CHOICES = [
        ('IN', 'Cash In'),
        ('OUT', 'Cash Out'),
        ('BOTH', 'Both'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=4, choices=TYPE_CHOICES, default='BOTH')

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

class Party(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='parties')
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        verbose_name_plural = "Parties"

    def __str__(self):
        return self.name

class PaymentMode(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='payment_modes')
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class Transaction(models.Model):
    TYPE_CHOICES = [
        ('IN', 'Cash In'),
        ('OUT', 'Cash Out'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cashbook = models.ForeignKey(Cashbook, on_delete=models.CASCADE, related_name='transactions')
    type = models.CharField(max_length=3, choices=TYPE_CHOICES)
    amount = models.DecimalField(max_digits=19, decimal_places=2)
    remark = models.TextField(blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    party = models.ForeignKey(Party, on_delete=models.SET_NULL, null=True, blank=True)
    payment_mode = models.ForeignKey(PaymentMode, on_delete=models.SET_NULL, null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    transaction_date = models.DateField(auto_now_add=True) # Added for filtering by date
    transaction_time = models.TimeField(auto_now_add=True) # Added for filtering by time

    class Meta:
        indexes = [
            models.Index(fields=['cashbook', 'created_at']),
        ]

    def __str__(self):
        return f"{self.type} - {self.amount}"
