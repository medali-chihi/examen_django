# logs/notifications.py

from django.core.mail import send_mail
from django.conf import settings

def send_notification(subject, message, recipient_list):
    """
    Envoie une notification par email.
    
    :param subject: Sujet de l'email
    :param message: Contenu de l'email
    :param recipient_list: Liste des destinataires
    """
    send_mail(
        subject,
        message,
        settings.EMAIL_HOST_USER,  # Utilise l'email configuré dans settings.py
        recipient_list,
        fail_silently=False,
    )