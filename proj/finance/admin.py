from django.contrib import admin

from .models import Wallet, Transaction


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ("id", "owner", "balance", "currency", "is_active", "created_at")
    list_filter = ("is_active", "currency")
    search_fields = ("owner",)
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("id", "sender_wallet", "receiver_wallet", "amount", "commission_amount", "currency", "created_at")
    list_filter = ("currency",)
    search_fields = ("sender_wallet__owner", "receiver_wallet__owner")
    readonly_fields = ("id", "created_at")
