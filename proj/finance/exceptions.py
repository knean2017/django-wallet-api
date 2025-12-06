class TransferError(Exception):
    """Base exception for transfer workflow."""


class WalletNotFoundError(TransferError):
    """Raised when any referenced wallet is missing."""

    def __init__(self, wallet_id: str) -> None:
        super().__init__(f"Wallet {wallet_id} does not exist.")
        self.wallet_id = wallet_id


class WalletInactiveError(TransferError):
    """Raised when attempting to use a disabled wallet."""

    def __init__(self, wallet_id: str) -> None:
        super().__init__(f"Wallet {wallet_id} is inactive.")
        self.wallet_id = wallet_id


class InsufficientFundsError(TransferError):
    """Raised when payer wallet lacks enough balance."""

    def __init__(self, wallet_id: str) -> None:
        super().__init__(f"Wallet {wallet_id} has insufficient funds.")
        self.wallet_id = wallet_id

