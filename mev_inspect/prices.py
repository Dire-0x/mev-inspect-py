import logging
import time
from datetime import datetime
from typing import Dict, List

from pycoingecko import CoinGeckoAPI

from mev_inspect.crud.prices import get_prices, write_prices
from mev_inspect.schemas.prices import COINGECKO_ID_BY_ADDRESS, TOKEN_ADDRESSES, Price

logger = logging.getLogger(__name__)


def fetch_prices(db_session) -> List[Price]:
    coingecko_api = CoinGeckoAPI()
    prices = []

    for token_address in TOKEN_ADDRESSES:
        logger.info(f"Get Price Data for: {token_address}")
        coingecko_price_data = coingecko_api.get_coin_market_chart_by_id(
            id=COINGECKO_ID_BY_ADDRESS[token_address],
            vs_currency="usd",
            days="max",
            interval="daily",
        )
        price = _build_token_prices(coingecko_price_data, token_address)
        if db_session:
            write_prices(db_session, price)
            logger.info(f"saved price data for: {token_address}")
        prices += price
        time.sleep(1.2)
    return prices


def fetch_prices_range(after: datetime, before: datetime) -> List[Price]:
    coingecko_api = CoinGeckoAPI()
    prices = []
    after_unix = int(after.timestamp())
    before_unix = int(before.timestamp())

    for token_address in TOKEN_ADDRESSES:
        coingecko_price_data = coingecko_api.get_coin_market_chart_range_by_id(
            COINGECKO_ID_BY_ADDRESS[token_address], "usd", after_unix, before_unix
        )

        prices += _build_token_prices(coingecko_price_data, token_address)

    return prices


def _build_token_prices(coingecko_price_data, token_address) -> List[Price]:
    time_series = coingecko_price_data["prices"]
    prices = []
    for entry in time_series:
        timestamp = datetime.fromtimestamp(entry[0] / 1000)
        token_price = entry[1]
        prices.append(
            Price(
                timestamp=timestamp,
                usd_price=token_price,
                token_address=token_address,
            )
        )
    return prices


def get_prices_map(db_session, tokens: List[str]) -> Dict[str, List[Price]]:
    pricesMap: Dict[str, List[Price]] = {}
    prices = get_prices(db_session, tokens)
    for price in prices:
        if price.token_address not in pricesMap.keys():
            pricesMap[price.token_address] = []
        pricesMap[price.token_address].append(price)
    return pricesMap


def get_closest_price(timestamp: float, prices: List[Price]) -> Price:
    return prices[
        min(
            range(len(prices)),
            key=lambda i: abs(prices[i].timestamp.timestamp() - timestamp),
        )
    ]
