from __future__ import annotations

import argparse
import enum
import json
import logging
import os
import sys
from typing import Any, Dict, TypedDict

from trading_bot.bot.client import BinanceFuturesClient, BinanceFuturesClientConfig
from trading_bot.bot.env import load_project_dotenv
from trading_bot.bot.exceptions import BinanceAPIError, TradingBotError, ValidationError
from trading_bot.bot.logging_config import setup_logging
from trading_bot.bot.orders import build_order_params, place_order


class ExitCode(enum.IntEnum):
    SUCCESS = 0
    UNEXPECTED_ERROR = 1
    INPUT_ERROR = 2
    API_ERROR = 3


class BinanceOrderResponse(TypedDict, total=False):
    orderId: int
    status: str
    executedQty: str
    avgPrice: str
    avgFillPrice: str


def _json_dumps(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False)


def _get_env(name: str) -> str:
    v = os.getenv(name)
    if v is None or not v.strip():
        raise ValidationError(f"Missing required environment variable: {name}")
    return v.strip()


def _build_client() -> BinanceFuturesClient:
    base_url = os.getenv("BINANCE_FUTURES_TESTNET_BASE_URL", "https://testnet.binancefuture.com")
    api_key = _get_env("BINANCE_FUTURES_TESTNET_API_KEY")
    api_secret = _get_env("BINANCE_FUTURES_TESTNET_API_SECRET")
    cfg = BinanceFuturesClientConfig(base_url=base_url, api_key=api_key, api_secret=api_secret)
    return BinanceFuturesClient(cfg)


def _print_order_result(resp: Any) -> None:
    if resp is None:
        print("No response body.")
        return

    if isinstance(resp, dict):
        r: BinanceOrderResponse = resp  # best-effort typing for IDE support
        order_id = r.get("orderId")
        status = r.get("status")
        executed_qty = r.get("executedQty")
        avg_price = r.get("avgPrice") or r.get("avgFillPrice")

        print("\nOrder response (selected fields)")
        print(f"- orderId: {order_id}")
        print(f"- status: {status}")
        print(f"- executedQty: {executed_qty}")
        if avg_price is not None:
            print(f"- avgPrice: {avg_price}")

        print("\nFull response JSON")
        print(_json_dumps(resp))
    else:
        print("\nResponse")
        print(resp)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="trading_bot", description="Binance Futures Testnet order CLI")
    p.add_argument("--log-level", default="INFO", help="Logging level (DEBUG/INFO/WARNING/ERROR)")

    sub = p.add_subparsers(dest="command", required=True)
    order = sub.add_parser("order", help="Place an order (MARKET / LIMIT / STOP (stop-limit))")
    order.add_argument("--symbol", required=True, help="Symbol like BTCUSDT")
    order.add_argument("--side", required=True, choices=["BUY", "SELL"], help="BUY or SELL")
    order.add_argument("--type", required=True, choices=["MARKET", "LIMIT", "STOP"], help="Order type")
    order.add_argument("--quantity", required=True, help="Order quantity (positive number)")
    order.add_argument("--price", help="Price (required for LIMIT)")
    order.add_argument("--stop-price", help="Stop price (required for STOP / stop-limit)")
    order.add_argument("--time-in-force", default="GTC", help="LIMIT timeInForce (default: GTC)")
    order.add_argument(
        "--dry-run",
        action="store_true",
        help="Use /fapi/v1/order/test (validates but does not place an order)",
    )
    return p


def _validate_order_cli_args(args: argparse.Namespace) -> None:
    """
    CLI-level validation so user gets fast feedback before any API calls.
    (Argparse can't express these conditional requirements cleanly.)
    """
    if args.type == "LIMIT" and not args.price:
        raise ValidationError("--price is required when --type LIMIT is chosen")
    if args.type == "STOP":
        if not args.stop_price:
            raise ValidationError("--stop-price is required when --type STOP is chosen")
        if not args.price:
            raise ValidationError("--price is required when --type STOP is chosen")
    if args.type == "MARKET":
        if args.price:
            raise ValidationError("--price must not be provided when --type MARKET is chosen")
        if args.stop_price:
            raise ValidationError("--stop-price must not be provided when --type MARKET is chosen")
    if args.type == "LIMIT" and args.stop_price:
        raise ValidationError("--stop-price must not be provided when --type LIMIT is chosen")


def main(argv: list[str] | None = None) -> int:
    dotenv_path = load_project_dotenv(override=False)
    parser = build_parser()
    args = parser.parse_args(argv)

    log_path = setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    logger.info("Log file: %s", log_path)
    if dotenv_path is not None:
        logger.info("Loaded .env from: %s", dotenv_path)

    try:
        if args.command == "order":
            _validate_order_cli_args(args)
            summary: Dict[str, Any] = build_order_params(
                symbol=args.symbol,
                side=args.side,
                order_type=args.type,
                quantity=args.quantity,
                price=args.price,
                stop_price=args.stop_price,
                time_in_force=args.time_in_force,
            )
            print("Order request summary")
            print(_json_dumps(summary))

            client = _build_client()
            resp = place_order(
                client,
                symbol=args.symbol,
                side=args.side,
                order_type=args.type,
                quantity=args.quantity,
                price=args.price,
                stop_price=args.stop_price,
                time_in_force=args.time_in_force,
                dry_run=args.dry_run,
            )

            _print_order_result(resp)
            print("\nResult: SUCCESS")
            return int(ExitCode.SUCCESS)

        raise TradingBotError(f"Unknown command: {args.command}")

    except ValidationError as e:
        logger.warning("Invalid input: %s", e)
        print(f"\nResult: FAILED (invalid input) - {e}")
        return int(ExitCode.INPUT_ERROR)
    except BinanceAPIError as e:
        logger.error("Binance API error: %s", e)
        print(f"\nResult: FAILED (API error) - {e}")
        return int(ExitCode.API_ERROR)
    except Exception as e:
        logger.exception("Unexpected error")
        print(f"\nResult: FAILED (unexpected error) - {e.__class__.__name__}: {e}")
        return int(ExitCode.UNEXPECTED_ERROR)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

