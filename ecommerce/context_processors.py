from .models import Notification


def notifications(request):
    if request.user.is_authenticated and request.user.is_staff:
        unread_count = Notification.objects.filter(is_read=False).count()
        return {"unread_count": unread_count}
    return {"unread_count": 0}

