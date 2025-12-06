from rest_framework import views, status, serializers
from rest_framework.response import Response

from .serializers import TransferSerializer, TransactionSerializer
from .services import TransferService
from .exceptions import TransferError


class TransferView(views.APIView):
    def post(self, request):
        payload = TransferSerializer(data=request.data)
        payload.is_valid(raise_exception=True)

        try:
            transaction = TransferService().execute_transfer(
                sender_wallet_id=payload.validated_data["sender_wallet_id"],
                receiver_wallet_id=payload.validated_data["receiver_wallet_id"],
                amount=payload.validated_data["amount"],
            )
        except TransferError as exc:
            raise serializers.ValidationError({"detail": str(exc)}) from exc

        return Response(
            TransactionSerializer(transaction).data,
            status=status.HTTP_201_CREATED,
        )