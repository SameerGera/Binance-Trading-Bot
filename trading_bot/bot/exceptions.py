class TradingBotError(Exception):
    """Base exception for this project."""


class ValidationError(TradingBotError):
    pass


class BinanceAPIError(TradingBotError):
    def __init__(self, status_code: int, body: object):
        self.status_code = status_code
        self.body = body
        super().__init__(f"Binance API error ({status_code}): {body}")

