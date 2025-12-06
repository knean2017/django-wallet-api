from decimal import Decimal

from rest_framework import serializers

from .models import Wallet, Transaction


class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = (
            "id",
            "owner",
            "balance",
            "currency",
            "is_active",
            "created_at",
            "updated_at"
        )


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = (
            "id",
            "sender_wallet",
            "receiver_wallet",
            "amount",
            "commission_amount",
            "currency",
            "created_at"
        )


class TransferSerializer(serializers.Serializer):
    sender_wallet_id = serializers.UUIDField()
    receiver_wallet_id = serializers.UUIDField()
    amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0.01")
    )

    def validate(self, data):
        if data["sender_wallet_id"] == data["receiver_wallet_id"]:
            raise serializers.ValidationError("Sender and receiver wallets must be different.")
        return data