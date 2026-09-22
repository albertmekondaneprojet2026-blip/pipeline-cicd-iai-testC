"""
Fonction réutilisable pour envoyer une alerte par email,
utilisée à la fois par le gate IA (pipeline bloqué) et
par le monitoring de production (anomalie détectée).
"""

import os
import sys
from pathlib import Path


# =========================================================
# RACINE DU PROJET
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


# =========================================================
# CONFIGURATION DJANGO
# =========================================================

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()


# =========================================================
# IMPORTS
# =========================================================

from django.core.mail import send_mail
from django.conf import settings


# =========================================================
# ENVOI DE L'ALERTE
# =========================================================

def send_alert_email(subject: str, message: str) -> bool:
    """Envoie un email d'alerte. Retourne True si succès."""

    try:
        send_mail(
            subject=f"[TaskFlow Alerte] {subject}",
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.ALERT_RECIPIENT_EMAIL],
            fail_silently=False,
        )

        print("Alerte email envoyée avec succès.")
        return True

    except Exception as e:
        print(f" Échec de l'envoi de l'alerte email : {e}")
        return False


# =========================================================
# TEST DIRECT
# =========================================================

if __name__ == "__main__":

    import sys

    subject = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "Test"
    )

    message = (
        sys.argv[2]
        if len(sys.argv) > 2
        else "Message de test."
    )

    send_alert_email(subject, message)