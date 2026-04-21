from __future__ import annotations

from decimal import Decimal, InvalidOperation

from .exceptions import ValidationError

ALLOWED_SIDES = {"BUY", "SELL"}
ALLOWED_ORDER_TYPES = {"MARKET", "LIMIT", "STOP"}


def _to_decimal(value: str, field: str) -> Decimal:
    """Convert user input to Decimal or raise ValidationError."""
    try:
        d = Decimal(str(value))
    except (InvalidOperation, ValueError) as e:
        raise ValidationError(f"Invalid {field}: {value}") from e
    return d


def validate_symbol(symbol: str) -> str:
    """Validate and normalize a futures symbol like `BTCUSDT`."""
    if not symbol or not isinstance(symbol, str):
        raise ValidationError("symbol is required")
    s = symbol.strip().upper()
    if not s.isalnum():
        raise ValidationError("symbol must be alphanumeric, e.g. BTCUSDT")
    return s


def validate_side(side: str) -> str:
    """Validate and normalize order side (`BUY` or `SELL`)."""
    if not side:
        raise ValidationError("side is required")
    s = side.strip().upper()
    if s not in ALLOWED_SIDES:
        raise ValidationError(f"side must be one of {sorted(ALLOWED_SIDES)}")
    return s


def validate_order_type(order_type: str) -> str:
    """Validate and normalize order type (`MARKET`, `LIMIT`, `STOP`)."""
    if not order_type:
        raise ValidationError("type is required")
    t = order_type.strip().upper()
    if t not in ALLOWED_ORDER_TYPES:
        raise ValidationError(f"type must be one of {sorted(ALLOWED_ORDER_TYPES)}")
    return t


def validate_quantity(quantity: str) -> str:
    """Validate quantity as a positive Decimal and return a plain string."""
    q = _to_decimal(quantity, "quantity")
    if q <= 0:
        raise ValidationError("quantity must be > 0")
    return format(q, "f")


def validate_price(price: str) -> str:
    """Validate price as a positive Decimal and return a plain string."""
    p = _to_decimal(price, "price")
    if p <= 0:
        raise ValidationError("price must be > 0")
    return format(p, "f")


def validate_stop_price(stop_price: str) -> str:
    """Validate stop price as a positive Decimal and return a plain string."""
    sp = _to_decimal(stop_price, "stopPrice")
    if sp <= 0:
        raise ValidationError("stopPrice must be > 0")
    return format(sp, "f")

