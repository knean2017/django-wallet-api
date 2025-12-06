from decimal import Decimal

from django.test import TestCase
from django.conf import settings
from rest_framework.test import APIClient

from .models import Wallet


class TransferAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin_wallet, _ = Wallet.objects.get_or_create(
            owner=settings.ADMIN_WALLET_OWNER,
            defaults={"balance": Decimal("0.00")},
        )
        self.source = Wallet.objects.create(
            owner="alice",
            balance=Decimal("2000.00"),
        )
        self.destination = Wallet.objects.create(
            owner="bob",
            balance=Decimal("0.00"),
        )

    def test_transfer_with_commission(self):
        """
        Transfer 1500 from alice to bob.
        Commission: 1500 * 10% = 150
        Total deducted from alice: 1500 + 150 = 1650
        Alice final balance: 2000 - 1650 = 350
        Bob final balance: 0 + 1500 = 1500
        Admin final balance: 0 + 150 = 150
        """
        payload = {
            "sender_wallet_id": str(self.source.id),
            "receiver_wallet_id": str(self.destination.id),
            "amount": "1500.00",
        }

        response = self.client.post("/api/transfer/", payload, format="json")
        self.assertEqual(response.status_code, 201, response.content)

        self.source.refresh_from_db()
        self.destination.refresh_from_db()
        self.admin_wallet.refresh_from_db()

        self.assertEqual(self.source.balance, Decimal("350.00"))
        self.assertEqual(self.destination.balance, Decimal("1500.00"))
        self.assertEqual(self.admin_wallet.balance, Decimal("150.00"))

        self.assertEqual(response.data["commission_amount"], "150.00")

    def test_transfer_without_commission(self):
        """
        Transfer 500 from alice to bob (below 1000 threshold).
        No commission should be applied.
        """
        payload = {
            "sender_wallet_id": str(self.source.id),
            "receiver_wallet_id": str(self.destination.id),
            "amount": "500.00",
        }

        response = self.client.post("/api/transfer/", payload, format="json")
        self.assertEqual(response.status_code, 201, response.content)

        self.source.refresh_from_db()
        self.destination.refresh_from_db()
        self.admin_wallet.refresh_from_db()

        self.assertEqual(self.source.balance, Decimal("1500.00"))
        self.assertEqual(self.destination.balance, Decimal("500.00"))
        self.assertEqual(self.admin_wallet.balance, Decimal("0.00"))

    def test_transfer_rejects_insufficient_funds(self):
        """
        Try to transfer more than alice has - should fail.
        """
        payload = {
            "sender_wallet_id": str(self.source.id),
            "receiver_wallet_id": str(self.destination.id),
            "amount": "5000.00",
        }

        response = self.client.post("/api/transfer/", payload, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("detail", response.data)

    def test_transfer_rejects_same_wallet(self):
        """
        Cannot transfer to the same wallet.
        """
        payload = {
            "sender_wallet_id": str(self.source.id),
            "receiver_wallet_id": str(self.source.id),
            "amount": "100.00",
        }

        response = self.client.post("/api/transfer/", payload, format="json")
        self.assertEqual(response.status_code, 400)
