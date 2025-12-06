from decimal import Decimal
from django.db import transaction, connection
from django.conf import settings

from .models import Wallet, Transaction
from .exceptions import InsufficientFundsError, WalletInactiveError, WalletNotFoundError


class TransferService:
    def __init__(self):
        self.commission_rate = Decimal("0.10")
        self.commission_threshold = Decimal("1000")

    def execute_transfer(
        self,
        sender_wallet_id,
        receiver_wallet_id,
        amount: Decimal
    ) -> Transaction:
        """
        Orchestrates the transfer process atomically.
        """
        with transaction.atomic():
            wallets = self._get_locked_wallets(sender_wallet_id, receiver_wallet_id)
            sender = wallets['sender']
            receiver = wallets['receiver']
            admin = wallets['admin']

            commission_amount = self._calculate_commission(amount)
            total_amount = amount + commission_amount

            self._validate_wallets(sender, receiver)
            self._validate_balance(sender, total_amount)
            self._perform_wallet_updates(sender, receiver, admin, amount, commission_amount)

            txn = self._create_transaction_record(
                sender,
                receiver,
                amount,
                commission_amount
            )

            # Trigger side effects (async tasks)
            from .tasks import send_notification_task
            transaction.on_commit(lambda: send_notification_task.delay(str(txn.id)))

            return txn

    def _lock(self, queryset):
        if connection.features.has_select_for_update:
            return queryset.select_for_update()
        return queryset

    def _get_locked_wallets(self, sender_id, receiver_id) -> dict:
        """
        Locks and retrieves sender, receiver, and admin wallets to prevent race conditions.
        """
        admin_owner = settings.ADMIN_WALLET_OWNER

        # CRITICAL: Lock all rows in a single query and order them by PK ('id')
        # Ordering is crucial to prevent deadlocks (lock order inversion).
        locked_wallets = self._lock(Wallet.objects).filter(
            id__in=[sender_id, receiver_id]
        ).order_by('id')

        wallet_map = {w.id: w for w in locked_wallets}

        sender = wallet_map.get(sender_id)
        receiver = wallet_map.get(receiver_id)

        if not sender:
            raise WalletNotFoundError(sender_id)
        if not receiver:
            raise WalletNotFoundError(receiver_id)

        # Get admin wallet separately (by owner field)
        try:
            admin = self._lock(Wallet.objects).get(owner=admin_owner)
        except Wallet.DoesNotExist:
            raise WalletNotFoundError(admin_owner)

        return {
            "sender": sender,
            "receiver": receiver,
            "admin": admin
        }

    def _validate_wallets(self, sender: Wallet, receiver: Wallet):
        """
        Validates that wallets are active.
        """
        if not sender.is_active:
            raise WalletInactiveError(sender.id)
        if not receiver.is_active:
            raise WalletInactiveError(receiver.id)

    def _validate_balance(self, wallet: Wallet, required_amount: Decimal):
        """
        Validates that wallet has sufficient balance.
        """
        if wallet.balance < required_amount:
            raise InsufficientFundsError(wallet.id)

    def _calculate_commission(self, amount: Decimal) -> Decimal:
        """
        Calculates commission if amount exceeds threshold.
        """
        if amount >= self.commission_threshold:
            return amount * self.commission_rate
        return Decimal("0")

    def _perform_wallet_updates(
        self,
        sender: Wallet,
        receiver: Wallet,
        admin: Wallet,
        amount: Decimal,
        commission_amount: Decimal
    ):
        """
        Performs atomic wallet balance updates.
        """
        total_deduction = amount + commission_amount

        sender.balance -= total_deduction
        sender.save()

        receiver.balance += amount
        receiver.save()

        if commission_amount > 0:
            admin.balance += commission_amount
            admin.save()

    def _create_transaction_record(
        self,
        sender_wallet: Wallet,
        receiver_wallet: Wallet,
        amount: Decimal,
        commission_amount: Decimal
    ) -> Transaction:
        """
        Creates a transaction record.
        """
        return Transaction.objects.create(
            sender_wallet=sender_wallet,
            receiver_wallet=receiver_wallet,
            amount=amount,
            commission_amount=commission_amount,
            currency=sender_wallet.currency
        )