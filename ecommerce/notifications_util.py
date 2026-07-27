from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string


def send_notification_email(user, subject, message, order=None, request=None):
    if not user.email:
        return
    scheme = request.scheme if request else 'https'
    host = request.get_host() if request else 'localhost:8000'
    context = {
        'user': user,
        'message': message,
        'order': order,
        'scheme': scheme,
        'host': host,
    }
    html_message = render_to_string('ecommerce/email_notification.html', context)
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=True,
    )
