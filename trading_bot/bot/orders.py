from __future__ import annotations

from typing import Any, Dict, Optional

from .client import BinanceFuturesClient
from .exceptions import ValidationError
from .validators import (
    validate_order_type,
    validate_price,
    validate_quantity,
    validate_side,
    validate_stop_price,
    validate_symbol,
)


def build_order_params(
    *,
    symbol: str,
    side: str,
    order_type: str,
    quantity: str,
    price: Optional[str] = None,
    stop_price: Optional[str] = None,
    time_in_force: str = "GTC",
) -> Dict[str, Any]:
    """
    Build validated Binance Futures order parameters.

    Args:
        symbol: Symbol like "BTCUSDT".
        side: "BUY" or "SELL".
        order_type: "MARKET", "LIMIT", or "STOP" (stop-limit).
        quantity: Positive numeric value (string).
        price: Required for LIMIT and STOP.
        stop_price: Required for STOP.
        time_in_force: Binance `timeInForce` value for orders that require it.

    Returns:
        Dictionary suitable for signing and POSTing to Binance.
    """
    symbol_v = validate_symbol(symbol)
    side_v = validate_side(side)
    type_v = validate_order_type(order_type)
    qty_v = validate_quantity(quantity)

    params: Dict[str, Any] = {
        "symbol": symbol_v,
        "side": side_v,
        "type": type_v,
        "quantity": qty_v,
    }

    if type_v == "LIMIT":
        if price is None:
            raise ValidationError("price is required for LIMIT orders")
        params["price"] = validate_price(price)
        params["timeInForce"] = time_in_force

    if type_v == "STOP":
        if stop_price is None:
            raise ValidationError("stop_price is required for STOP (stop-limit) orders")
        if price is None:
            raise ValidationError("price is required for STOP (stop-limit) orders")
        params["stopPrice"] = validate_stop_price(stop_price)
        params["price"] = validate_price(price)
        params["timeInForce"] = time_in_force

    return params


def place_order(
    client: BinanceFuturesClient,
    *,
    symbol: str,
    side: str,
    order_type: str,
    quantity: str,
    price: Optional[str] = None,
    stop_price: Optional[str] = None,
    time_in_force: str = "GTC",
    dry_run: bool = False,
) -> Any:
    """
    Place (or dry-run) an order using the provided client.

    Args:
        client: Configured Binance Futures client.
        symbol: Symbol like "BTCUSDT".
        side: "BUY" or "SELL".
        order_type: "MARKET", "LIMIT", or "STOP".
        quantity: Positive numeric value (string).
        price: Required for LIMIT and STOP.
        stop_price: Required for STOP.
        time_in_force: Binance `timeInForce` value.
        dry_run: If True, uses `/fapi/v1/order/test`.

    Returns:
        Parsed response body (JSON dict) or raw text depending on API response.
    """
    params = build_order_params(
        symbol=symbol,
        side=side,
        order_type=order_type,
        quantity=quantity,
        price=price,
        stop_price=stop_price,
        time_in_force=time_in_force,
    )
    if dry_run:
        return client.test_order(params)
    return client.create_order(params)

