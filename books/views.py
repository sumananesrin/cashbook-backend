from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, F, Q
from .models import Business, Cashbook, Member, Category, Party, PaymentMode, Transaction
from .serializers import (
    BusinessSerializer, CashbookSerializer, MemberSerializer, 
    CategorySerializer, PartySerializer, PaymentModeSerializer, TransactionSerializer
)

class IsBusinessMember(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # Check if user is a member of the business associated with the object
        if isinstance(obj, Business):
            return obj.members.filter(user=request.user).exists() or obj.owner == request.user
        if hasattr(obj, 'business'):
            return obj.business.members.filter(user=request.user).exists() or obj.business.owner == request.user
        if hasattr(obj, 'cashbook'):
            return obj.cashbook.business.members.filter(user=request.user).exists() or obj.cashbook.business.owner == request.user
        return False

class BusinessViewSet(viewsets.ModelViewSet):
    serializer_class = BusinessSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Business.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

class CashbookViewSet(viewsets.ModelViewSet):
    serializer_class = CashbookSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # User can see cashbooks they own OR are a member of
        return Cashbook.objects.filter(
            Q(business__owner=self.request.user) | 
            Q(business__members__user=self.request.user)
        ).distinct()

    def perform_create(self, serializer):
        user = self.request.user
        # Logic: Use existing business or create a new one
        # If business_id is passed in context or params, better usage, but for now:
        business = Business.objects.filter(owner=user).first()
        
        if not business:
            # Create a default business for the user
            business_name = f"{user.username}'s Business"
            if hasattr(user, 'full_name') and user.full_name:
                 business_name = f"{user.full_name}'s Business"
            business = Business.objects.create(name=business_name, owner=user)
            
        serializer.save(business=business)

    @action(detail=True, methods=['patch'], url_path='set-default')
    def set_default(self, request, pk=None):
        cashbook = self.get_object()
        # Set all other cashbooks in this business to non-default
        Cashbook.objects.filter(business=cashbook.business).update(is_default=False)
        cashbook.is_default = True
        cashbook.save()
        return Response({'status': 'default set'})
    
    @action(detail=True, methods=['get'], url_path='user-role')
    def user_role(self, request, pk=None):
        """Get the user's role in this cashbook"""
        cashbook = self.get_object()
        user = request.user
        
        # Check if owner
        if cashbook.business.owner == user:
            return Response({'role': 'owner', 'can_create': True, 'can_edit': True, 'can_delete': True})
        
        # Check if member
        member = Member.objects.filter(business=cashbook.business, user=user).first()
        if member:
            can_create = member.role in ['admin', 'editor']
            can_edit = member.role in ['admin', 'editor']
            can_delete = member.role == 'admin'
            return Response({
                'role': member.role,
                'can_create': can_create,
                'can_edit': can_edit,
                'can_delete': can_delete
            })
        
        return Response({'error': 'No access'}, status=403)

class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['cashbook', 'type', 'category', 'party', 'payment_mode', 'created_by']
    search_fields = ['remark', 'amount']
    ordering_fields = ['transaction_date', 'created_at', 'amount']
    ordering = ['-created_at']  # Default: newest first

    def get_queryset(self):
        """Filter transactions based on cashbooks user has access to"""
        from datetime import datetime, timedelta
        from django.utils import timezone
        
        user = self.request.user
        # Get all cashbooks where user is owner or member
        queryset = Transaction.objects.filter(
            cashbook__business__owner=user
        ) | Transaction.objects.filter(
            cashbook__business__members__user=user
        )
        
        # Apply cashbook filter
        cashbook_id = self.request.query_params.get('cashbook')
        if cashbook_id:
            queryset = queryset.filter(cashbook_id=cashbook_id)
        
        # Apply duration filter
        duration = self.request.query_params.get('duration')
        today = timezone.now().date()
        
        if duration == 'TODAY':
            queryset = queryset.filter(transaction_date=today)
        elif duration == 'LAST_7_DAYS':
            start_date = today - timedelta(days=7)
            queryset = queryset.filter(transaction_date__gte=start_date)
        elif duration == 'LAST_30_DAYS':
            start_date = today - timedelta(days=30)
            queryset = queryset.filter(transaction_date__gte=start_date)
        elif duration == 'THIS_MONTH':
            queryset = queryset.filter(
                transaction_date__year=today.year,
                transaction_date__month=today.month
            )
        # ALL_TIME (default) - no filter needed
        
        # Apply member filter (convert Member ID to User)
        member_id = self.request.query_params.get('member')
        if member_id:
            try:
                member_obj = Member.objects.get(id=member_id)
                queryset = queryset.filter(created_by=member_obj.user)
            except (Member.DoesNotExist, ValueError):
                queryset = queryset.none()
        
        # Filter by date range (custom date range if provided)
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(transaction_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(transaction_date__lte=end_date)
        
        return queryset.distinct()

    def list(self, request, *args, **kwargs):
        """List transactions with running balance calculated"""
        queryset = self.filter_queryset(self.get_queryset())
        
        # For running balance, we need to order by date ascending
        transactions_ordered = queryset.order_by('transaction_date', 'created_at')
        
        # Calculate running balance
        running_balance = 0
        transactions_with_balance = []
        
        for txn in transactions_ordered:
            if txn.type == 'IN':
                running_balance += txn.amount
            else:  # OUT
                running_balance -= txn.amount
            
            # Attach running balance to transaction
            txn.running_balance = running_balance
            transactions_with_balance.append(txn)
        
        # Reverse to show newest first
        transactions_with_balance.reverse()
        
        # Paginate
        page = self.paginate_queryset(transactions_with_balance)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(transactions_with_balance, many=True)
        return Response(serializer.data)

    def perform_create(self, serializer):
        """Create transaction with permission check"""
        user = self.request.user
        cashbook = serializer.validated_data['cashbook']
        
        # Check if user has access to this cashbook
        is_owner = cashbook.business.owner == user
        member = Member.objects.filter(business=cashbook.business, user=user).first()
        
        if not is_owner and not member:
            raise permissions.PermissionDenied("You do not have access to this cashbook.")
        
        # Check if user has permission to create transactions
        if member and member.role == 'VIEWER':
            raise permissions.PermissionDenied("Viewers cannot create transactions.")
        
        serializer.save(created_by=user)

    def perform_update(self, serializer):
        """Update transaction with permission check"""
        user = self.request.user
        transaction = self.get_object()
        cashbook = transaction.cashbook
        
        is_owner = cashbook.business.owner == user
        member = Member.objects.filter(business=cashbook.business, user=user).first()
        
        if not is_owner and not member:
            raise permissions.PermissionDenied("You do not have access to this cashbook.")
        
        if member and member.role == 'VIEWER':
            raise permissions.PermissionDenied("Viewers cannot edit transactions.")
        
        serializer.save()

    def perform_destroy(self, instance):
        """Delete transaction with permission check"""
        user = self.request.user
        cashbook = instance.cashbook
        
        is_owner = cashbook.business.owner == user
        member = Member.objects.filter(business=cashbook.business, user=user).first()
        
        if not is_owner and not member:
            raise permissions.PermissionDenied("You do not have access to this cashbook.")
        
        # Only admins/owners can delete
        if member and member.role != 'ADMIN':
            raise permissions.PermissionDenied("Only admins can delete transactions.")
        
        instance.delete()

class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Category.objects.filter(business__owner=user) | Category.objects.filter(business__members__user=user)

    def perform_create(self, serializer):
        business = serializer.validated_data['business']
        user = self.request.user
        
        is_owner = business.owner == user
        is_member = business.members.filter(user=user).exists()
        
        if not is_owner and not is_member:
            raise permissions.PermissionDenied("You do not have access to this business.")
            
        # Check specific role if member (e.g., viewers can't create)
        if is_member:
            member = business.members.get(user=user)
            if member.role == 'VIEWER':
                 raise permissions.PermissionDenied("Viewers cannot create categories.")
                 
        serializer.save()

class PartyViewSet(viewsets.ModelViewSet):
    serializer_class = PartySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Party.objects.filter(business__owner=user) | Party.objects.filter(business__members__user=user)

    def perform_create(self, serializer):
        business = serializer.validated_data['business']
        user = self.request.user
        
        is_owner = business.owner == user
        is_member = business.members.filter(user=user).exists()
        
        if not is_owner and not is_member:
            raise permissions.PermissionDenied("You do not have access to this business.")
            
        if is_member:
            member = business.members.get(user=user)
            if member.role == 'VIEWER':
                 raise permissions.PermissionDenied("Viewers cannot create parties.")
                 
        serializer.save()

class PaymentModeViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentModeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return PaymentMode.objects.filter(business__owner=user) | PaymentMode.objects.filter(business__members__user=user)

    def perform_create(self, serializer):
        business = serializer.validated_data['business']
        user = self.request.user
        
        is_owner = business.owner == user
        is_member = business.members.filter(user=user).exists()
        
        if not is_owner and not is_member:
            raise permissions.PermissionDenied("You do not have access to this business.")
            
        if is_member:
            member = business.members.get(user=user)
            if member.role == 'VIEWER':
                 raise permissions.PermissionDenied("Viewers cannot create payment modes.")
                 
        serializer.save()

class MemberViewSet(viewsets.ModelViewSet):
    serializer_class = MemberSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Member.objects.filter(business__owner=self.request.user)

from rest_framework.views import APIView

class SummaryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from datetime import datetime, timedelta
        from django.utils import timezone
        from django.db.models import Q
        
        cashbook_id = request.query_params.get('cashbook')
        if not cashbook_id:
            return Response({'error': 'cashbook_id required'}, status=400)
        
        # Verify ownership or membership
        cashbook_exists = Cashbook.objects.filter(
            Q(id=cashbook_id, business__owner=request.user) |
            Q(id=cashbook_id, business__members__user=request.user)
        ).exists()
        
        if not cashbook_exists:
            return Response({'error': 'Cashbook not found or access denied'}, status=404)

        # Start with base queryset
        transactions = Transaction.objects.filter(cashbook_id=cashbook_id)
        
        # Apply duration filter
        duration = request.query_params.get('duration')
        today = timezone.now().date()
        
        if duration == 'TODAY':
            transactions = transactions.filter(transaction_date=today)
        elif duration == 'LAST_7_DAYS':
            start_date = today - timedelta(days=7)
            transactions = transactions.filter(transaction_date__gte=start_date)
        elif duration == 'LAST_30_DAYS':
            start_date = today - timedelta(days=30)
            transactions = transactions.filter(transaction_date__gte=start_date)
        elif duration == 'THIS_MONTH':
            transactions = transactions.filter(
                transaction_date__year=today.year,
                transaction_date__month=today.month
            )
        # ALL_TIME (default) - no filter needed
        
        # Apply type filter
        txn_type = request.query_params.get('type')
        if txn_type:
            transactions = transactions.filter(type=txn_type)
        
        # Apply category filter
        category = request.query_params.get('category')
        if category:
            transactions = transactions.filter(category_id=category)
        
        # Apply party filter
        party = request.query_params.get('party')
        if party:
            transactions = transactions.filter(party_id=party)
        
        # Apply member filter
        member_id = request.query_params.get('member')
        if member_id:
            try:
                member_obj = Member.objects.get(id=member_id)
                transactions = transactions.filter(created_by=member_obj.user)
            except (Member.DoesNotExist, ValueError):
                # If invalid member ID, return empty or ignore? Let's return empty to be safe
                transactions = transactions.none()
        
        # Apply payment mode filter
        payment_mode = request.query_params.get('payment_mode')
        if payment_mode:
            transactions = transactions.filter(payment_mode_id=payment_mode)
        
        # Apply search filter
        search = request.query_params.get('search')
        if search:
            transactions = transactions.filter(
                Q(remark__icontains=search) | Q(amount__icontains=search)
            )
        
        # Calculate totals
        total_in = transactions.filter(type='IN').aggregate(Sum('amount'))['amount__sum'] or 0
        total_out = transactions.filter(type='OUT').aggregate(Sum('amount'))['amount__sum'] or 0
        net_balance = total_in - total_out

        return Response({
            'total_in': total_in,
            'total_out': total_out,
            'net_balance': net_balance
        })
