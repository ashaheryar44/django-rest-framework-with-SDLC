from celery import shared_task
from .models import Loan
from django.core.mail import send_mail
from django.conf import settings

from django.utils import timezone


@shared_task
def send_loan_notification(loan_id):
    try:
        loan = Loan.objects.get(id=loan_id)
        member_email = loan.member.user.email
        book_title = loan.book.title
        send_mail(
            subject='Book Loaned Successfully',
            message=f'Hello {loan.member.user.username},\n\nYou have successfully loaned "{book_title}".\nPlease return it by the due date.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[member_email],
            fail_silently=False,
        )
    except Loan.DoesNotExist:
        pass


@shared_task
def send_over_due_loan_notification():
    try:
        loans = Loan.objects.filter(return_date=False, due_date__lt=timezone.now())
        if loans:
            for loan in loans:
                send_loan_notification(loan.id)

    except Loan.DoesNotExist:
        pass



