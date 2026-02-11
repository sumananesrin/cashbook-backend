from django.contrib import admin
from django.utils.html import format_html
from .models import Business, Cashbook, Member, Category, Party, PaymentMode, Transaction


# ============================================
# Business Admin
# ============================================
@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'owner', 'created_at')
    list_display_links = ('id', 'name')
    search_fields = ('name', 'owner__username', 'owner__full_name')
    list_filter = ('created_at',)
    readonly_fields = ('id', 'created_at')
    list_per_page = 25
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'owner')
        }),
        ('Metadata', {
            'fields': ('id', 'created_at'),
            'classes': ('collapse',)
        }),
    )


# ============================================
# Cashbook Admin
# ============================================
@admin.register(Cashbook)
class CashbookAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'get_owner', 'business', 'is_default', 'created_at')
    list_display_links = ('id', 'name')
    search_fields = ('name', 'business__name', 'business__owner__username')
    list_filter = ('is_default', 'business', 'created_at')
    readonly_fields = ('id', 'created_at')
    list_per_page = 25
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'business', 'is_default')
        }),
        ('Metadata', {
            'fields': ('id', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_owner(self, obj):
        """Display the business owner"""
        return obj.business.owner.username
    get_owner.short_description = 'Owner'
    get_owner.admin_order_field = 'business__owner__username'


# ============================================
# Member Admin
# ============================================
@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'get_user_full_name', 'business', 'role', 'joined_at')
    list_display_links = ('id', 'user')
    search_fields = ('user__username', 'user__full_name', 'business__name')
    list_filter = ('role', 'joined_at', 'business')
    readonly_fields = ('id', 'joined_at')
    list_per_page = 25
    ordering = ('-joined_at',)
    
    fieldsets = (
        ('Membership Information', {
            'fields': ('user', 'business', 'role')
        }),
        ('Metadata', {
            'fields': ('id', 'joined_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_user_full_name(self, obj):
        """Display user's full name"""
        return obj.user.full_name or '-'
    get_user_full_name.short_description = 'Full Name'
    get_user_full_name.admin_order_field = 'user__full_name'


# ============================================
# Category Admin
# ============================================
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'business', 'type', 'get_type_badge')
    list_display_links = ('id', 'name')
    search_fields = ('name', 'business__name')
    list_filter = ('type', 'business')
    readonly_fields = ('id',)
    list_per_page = 25
    ordering = ('name',)
    
    fieldsets = (
        ('Category Information', {
            'fields': ('name', 'business', 'type')
        }),
        ('Metadata', {
            'fields': ('id',),
            'classes': ('collapse',)
        }),
    )
    
    def get_type_badge(self, obj):
        """Display colored badge for category type"""
        colors = {
            'IN': '#28a745',
            'OUT': '#dc3545',
            'BOTH': '#007bff',
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-size: 11px;">{}</span>',
            colors.get(obj.type, '#6c757d'),
            obj.get_type_display()
        )
    get_type_badge.short_description = 'Type Badge'


# ============================================
# Party Admin
# ============================================
@admin.register(Party)
class PartyAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'business', 'phone')
    list_display_links = ('id', 'name')
    search_fields = ('name', 'business__name', 'phone')
    list_filter = ('business',)
    readonly_fields = ('id',)
    list_per_page = 25
    ordering = ('name',)
    
    fieldsets = (
        ('Party Information', {
            'fields': ('name', 'business', 'phone')
        }),
        ('Metadata', {
            'fields': ('id',),
            'classes': ('collapse',)
        }),
    )


# ============================================
# Payment Mode Admin
# ============================================
@admin.register(PaymentMode)
class PaymentModeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'business')
    list_display_links = ('id', 'name')
    search_fields = ('name', 'business__name')
    list_filter = ('business',)
    readonly_fields = ('id',)
    list_per_page = 25
    ordering = ('name',)
    
    fieldsets = (
        ('Payment Mode Information', {
            'fields': ('name', 'business')
        }),
        ('Metadata', {
            'fields': ('id',),
            'classes': ('collapse',)
        }),
    )


# ============================================
# Transaction Admin
# ============================================
@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        'id', 
        'transaction_date', 
        'transaction_time',
        'get_type_badge',
        'get_amount_display',
        'cashbook',
        'category',
        'party',
        'payment_mode',
        'created_by',
        'created_at'
    )
    list_display_links = ('id', 'transaction_date')
    search_fields = (
        'remark',
        'cashbook__name',
        'party__name',
        'category__name',
        'created_by__username'
    )
    list_filter = (
        'type',
        'transaction_date',
        'cashbook',
        'category',
        'payment_mode',
        'created_at'
    )
    readonly_fields = ('id', 'created_at', 'transaction_date', 'transaction_time')
    list_per_page = 25
    ordering = ('-transaction_date', '-transaction_time')
    date_hierarchy = 'transaction_date'
    
    fieldsets = (
        ('Transaction Details', {
            'fields': ('cashbook', 'type', 'amount', 'remark')
        }),
        ('Related Information', {
            'fields': ('category', 'party', 'payment_mode')
        }),
        ('Metadata', {
            'fields': ('id', 'created_by', 'transaction_date', 'transaction_time', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_type_badge(self, obj):
        """Display colored badge for transaction type"""
        if obj.type == 'IN':
            color = '#28a745'  # Green for Cash In
        else:
            color = '#dc3545'  # Red for Cash Out
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_type_display()
        )
    get_type_badge.short_description = 'Type'
    get_type_badge.admin_order_field = 'type'
    
    def get_amount_display(self, obj):
        """Display amount with currency symbol and color coding"""
        if obj.type == 'IN':
            color = '#28a745'
            prefix = '+'
        else:
            color = '#dc3545'
            prefix = '-'
        
        # Convert Decimal to float for proper formatting
        amount_value = float(obj.amount)
        
        # Format amount as string first to avoid format_html issues
        formatted_amount = f"{obj.amount:,.2f}"
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} ${}</span>',
            color,
            prefix,
            formatted_amount
        )
    get_amount_display.short_description = 'Amount'
    get_amount_display.admin_order_field = 'amount'

