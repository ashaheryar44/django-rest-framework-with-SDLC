import json
from datetime import timedelta

from django.db.models import Q
from django.db.models.aggregates import Count
from rest_framework.pagination import PageNumberPagination

from django.core.serializers import serialize
from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import Author, Book, Member, Loan
from .serializers import AuthorSerializer, BookSerializer, MemberSerializer, LoanSerializer
from rest_framework.decorators import action
from django.utils import timezone
from .tasks import send_loan_notification

# Define the configuration class within views.py
class StandardResultsPagination(PageNumberPagination):
    # Set how many items you want per page
    page_size = 10
    # Optional: allows the client to request a specific page size (e.g., ?page_size=25)
    page_size_query_param = 'page_size'
    # Optional: set an upper limit on the client requested page size
    max_page_size = 100

class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer

class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.select_related('author').all()
    serializer_class = BookSerializer
    pagination_class = StandardResultsPagination

    @action(detail=True, methods=['post'])
    def loan(self, request, pk=None):
        book = self.get_object()
        if book.available_copies < 1:
            return Response({'error': 'No available copies.'}, status=status.HTTP_400_BAD_REQUEST)
        member_id = request.data.get('member_id')
        try:
            member = Member.objects.get(id=member_id)
        except Member.DoesNotExist:
            return Response({'error': 'Member does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
        loan = Loan.objects.create(book=book, member=member)
        book.available_copies -= 1
        book.save()
        send_loan_notification.delay(loan.id)
        return Response({'status': 'Book loaned successfully.'}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def return_book(self, request, pk=None):
        book = self.get_object()
        member_id = request.data.get('member_id')
        try:
            loan = Loan.objects.get(book=book, member__id=member_id, is_returned=False)
        except Loan.DoesNotExist:
            return Response({'error': 'Active loan does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
        loan.is_returned = True
        loan.return_date = timezone.now().date()
        loan.save()
        book.available_copies += 1
        book.save()
        return Response({'status': 'Book returned successfully.'}, status=status.HTTP_200_OK)

class MemberViewSet(viewsets.ModelViewSet):
    queryset = Member.objects.all()
    serializer_class = MemberSerializer

class MemberTopActiveLoanViewSet(viewsets.ModelViewSet):
    queryset = Member.objects.all()
    serializer_class = MemberSerializer

    def get(self, request):
        query = self.queryset.annotate(
            active_loans=Count(
                'loan',
                filter=Q(loan__is_returned=False)
            )
        )

        if query:
            re
class LoanViewSet(viewsets.ModelViewSet):
    queryset = Loan.objects.all()
    serializer_class = LoanSerializer

    def post(self, request):
        try:
            body = json.loads(request.body)
            additional_days = int(body.get('additional_days'))
            loan_id = body.get('loan_id')

            if not additional_days and additional_days < 1:
                return Response({'error': 'Invalid value additional days'}, status=status.HTTP_400_BAD_REQUEST)

            obj = Loan.objects.filter(id=loan_id).first()
            if obj.due_date < timezone.now().date():
                return Response({'error': 'Due date cannot be in the future'}, status=status.HTTP_400_BAD_REQUEST)

            if not obj:
                return Response({'error': 'Loan does not exist.'}, status=status.HTTP_400_BAD_REQUEST)

            obj.due_date = obj.due_date + timedelta(days=additional_days)
            obj.save()
            serializer =  LoanSerializer(instance=obj)
            return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
        except Exception as e:
            return Response({'error': f'Something went wrong.{e}'}, status=status.HTTP_400_BAD_REQUEST)






