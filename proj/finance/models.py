from uuid import uuid4

from django.db import models
from django.core.validators import MinValueValidator


class Wallet(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4 ,editable=False)
    owner = models.CharField(max_length=100, unique=True)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default="USD")
    
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("owner",)

    def __str__(self):
        return f"Wallet of {self.owner} - Balance: {self.balance} {self.currency}"
    
class Transaction(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid4 ,editable=False)
    sender_wallet = models.ForeignKey(
        Wallet,
        on_delete=models.PROTECT,
        related_name="sent_transactions"
    )
    receiver_wallet = models.ForeignKey(
        Wallet,
        on_delete=models.PROTECT,
        related_name="received_transactions"
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    commission_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )

    currency = models.CharField(max_length=3, default="USD")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"Transaction {self.id} - {self.amount} {self.currency} from {self.sender_wallet.owner} to {self.receiver_wallet.owner}"
    