from rest_framework import serializers
from .models import Business, Cashbook, Member, Category, Party, PaymentMode, Transaction

class BusinessSerializer(serializers.ModelSerializer):
    class Meta:
        model = Business
        fields = '__all__'
        read_only_fields = ('owner', 'created_at')

class CashbookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cashbook
        fields = '__all__'
        read_only_fields = ('created_at',)

class MemberSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    name = serializers.SerializerMethodField()
    user_id = serializers.UUIDField(source='user.id', read_only=True)
    
    class Meta:
        model = Member
        fields = '__all__'
        read_only_fields = ('joined_at',)

    def get_name(self, obj):
        return obj.user.full_name or obj.user.email

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'
        # business is required for creation

class PartySerializer(serializers.ModelSerializer):
    class Meta:
        model = Party
        fields = '__all__'
        # business is required for creation

class PaymentModeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMode
        fields = '__all__'
        # business is required for creation

class TransactionSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    party_name = serializers.CharField(source='party.name', read_only=True)
    payment_mode_name = serializers.CharField(source='payment_mode.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    running_balance = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True, required=False)

    class Meta:
        model = Transaction
        fields = '__all__'
        read_only_fields = ('created_by', 'created_at', 'transaction_date', 'transaction_time', 'running_balance')

    def validate_amount(self, value):
        """Ensure amount is positive"""
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than 0")
        return value

    def validate(self, data):
        """Ensure required fields are present"""
        if not data.get('category'):
            raise serializers.ValidationError({"category": "Category is required"})
        if not data.get('payment_mode'):
            raise serializers.ValidationError({"payment_mode": "Payment mode is required"})
        if not data.get('amount'):
            raise serializers.ValidationError({"amount": "Amount is required"})
        return data
