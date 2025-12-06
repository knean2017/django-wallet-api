from django.apps import apps
from django.conf import settings
from django.db.models.signals import post_migrate
from django.dispatch import receiver


@receiver(post_migrate)
def ensure_admin_wallet(sender, **kwargs):
    """
    Ensure the admin wallet exists after migrations.
    """
    if sender.name != "finance":
        return

    Wallet = apps.get_model("finance", "Wallet")
    Wallet.objects.get_or_create(
        owner=settings.ADMIN_WALLET_OWNER,
        defaults={"currency": "USD"},
    )
