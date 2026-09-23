import logging
import threading

from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


def send_notification_email(user, subject, message, order=None, request=None):
    if not user.email:
        return

    recipient = user.email
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

    thread = threading.Thread(
        target=_send_email,
        args=(recipient, subject, message, html_message),
        daemon=True,
    )
    thread.start()


def _send_email(recipient, subject, message, html_message):
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
            html_message=html_message,
            fail_silently=False,
        )
    except Exception:
        logger.exception("Failed to send notification email to %s", recipient)
