import logging
import math
import sys
import traceback
from decimal import Decimal
from typing import List, Optional

from mev_inspect.block import get_blocks_map
from mev_inspect.crud.sandwiches import (
    count_sandwiches,
    fetch_sandwiches,
    update_sandwiches,
)
from mev_inspect.prices import get_closest_price, get_prices_map
from mev_inspect.schemas.sandwiches import Sandwich
from mev_inspect.schemas.swaps import Swap
from mev_inspect.tokens import get_token, get_tokens_map

logger = logging.getLogger(__name__)

UNISWAP_V2_ROUTER = "0x7a250d5630b4cf539739df2c5dacb4c659f2488d"
UNISWAP_V3_ROUTER = "0xe592427a0aece92de3edee1f18e0157c05861564"
UNISWAP_V3_ROUTER_2 = "0x68b3465833fb72a70ecdf485e0e4c7bd8665fc45"


def get_sandwiches(swaps: List[Swap], db_session) -> List[Sandwich]:
    ordered_swaps = list(
        sorted(
            swaps,
            key=lambda swap: (swap.transaction_position, swap.trace_address),
        )
    )

    sandwiches: List[Sandwich] = []

    for index, swap in enumerate(ordered_swaps):
        rest_swaps = ordered_swaps[index + 1 :]
        sandwich = _get_sandwich_starting_with_swap(swap, rest_swaps, db_session)

        if sandwich is not None:
            sandwiches.append(sandwich)

    return sandwiches


def _get_sandwich_starting_with_swap(
    front_swap: Swap, rest_swaps: List[Swap], db_session
) -> Optional[Sandwich]:
    sandwicher_address = front_swap.to_address
    sandwiched_swaps = []

    if sandwicher_address in [
        UNISWAP_V2_ROUTER,
        UNISWAP_V3_ROUTER,
        UNISWAP_V3_ROUTER_2,
    ]:
        return None

    for other_swap in rest_swaps:

        if other_swap.transaction_hash == front_swap.transaction_hash:
            continue

        if other_swap.contract_address == front_swap.contract_address:
            if (
                other_swap.token_in_address == front_swap.token_in_address
                and other_swap.token_out_address == front_swap.token_out_address
                and other_swap.from_address != sandwicher_address
            ):
                sandwiched_swaps.append(other_swap)
            elif (
                other_swap.token_out_address == front_swap.token_in_address
                and other_swap.token_in_address == front_swap.token_out_address
                and other_swap.from_address == sandwicher_address
            ):
                if len(sandwiched_swaps) > 0:
                    profit = calculate_sandwich_profit(
                        front_swap, other_swap, db_session
                    )
                    return Sandwich(
                        block_number=front_swap.block_number,
                        sandwicher_address=sandwicher_address,
                        frontrun_swap=front_swap,
                        backrun_swap=other_swap,
                        sandwiched_swaps=sandwiched_swaps,
                        profit_token_address=front_swap.token_in_address,
                        profit_amount=profit if profit else 0,
                    )

    return None


def calculate_sandwich_profit(
    frontrun_swap: Swap, backrun_swap: Swap, db_session
) -> int:

    front_token_in = get_token(db_session, frontrun_swap.token_in_address)
    front_token_out = get_token(db_session, frontrun_swap.token_out_address)
    if not front_token_in or not front_token_out:
        return 0
    front_in_decimal = Decimal(10 ** front_token_in.decimals)
    front_out_decimal = Decimal(10 ** front_token_out.decimals)
    front_in_amount = frontrun_swap.token_in_amount / front_in_decimal
    front_out_amount = frontrun_swap.token_out_amount / front_out_decimal
    back_in_amount = backrun_swap.token_in_amount / front_out_decimal
    back_out_amount = backrun_swap.token_out_amount / front_in_decimal

    in_price = front_in_amount / front_out_amount
    if front_out_amount > front_in_amount:
        in_price = front_out_amount / front_in_amount

    out_price = back_in_amount / back_out_amount
    prices_flipped = False
    if back_out_amount > back_in_amount:
        out_price = back_out_amount / back_in_amount
        prices_flipped = True

    profit_decimal = Decimal(0)

    if back_in_amount > front_out_amount:
        if prices_flipped:
            profit_decimal = front_out_amount * (out_price - in_price)
        else:
            profit_decimal = front_out_amount / out_price - front_out_amount / in_price

    if back_in_amount < front_out_amount:
        profit_decimal = (
            1 - min(in_price, out_price) / max(in_price, out_price)
        ) * back_out_amount

    if back_in_amount == front_out_amount:
        profit_decimal = back_out_amount - front_in_amount

    profit = math.floor(profit_decimal * front_in_decimal)

    # logger.info(f"front {frontrun_swap.transaction_hash} {frontrun_swap.trace_address}")
    # logger.info(f"back {backrun_swap.transaction_hash} {backrun_swap.trace_address}")
    # logger.info(f"prices flipped {prices_flipped}")
    # logger.info(f"front in token {frontrun_swap.token_in_address}")
    # logger.info(f"front out token {frontrun_swap.token_out_address}")
    # logger.info(f"back in token {backrun_swap.token_in_address}")
    # logger.info(f"back out token {backrun_swap.token_out_address}")
    # logger.info(f"front_in_decimal {front_in_decimal}")
    # logger.info(f"front_out_decimal {front_out_decimal}")
    # logger.info(f"front_in_amount {front_in_amount}")
    # logger.info(f"front_out_amount {front_out_amount}")
    # logger.info(f"back_in_amount {back_in_amount}")
    # logger.info(f"back_out_amount {back_out_amount}")
    # logger.info(f"in_price {in_price}")
    # logger.info(f"out_price {out_price}")
    # logger.info(f"profit_decimal {profit_decimal}")
    # logger.info(f"profit {profit}")

    return profit


def update_sandwich_profit_usd(
    db_session, query: str = "profit_amount IS NOT NULL"
) -> None:
    logger.info("start update sandwich profit usd")

    allTokens = get_tokens_map(db_session)

    limit = 100
    skip = 0
    count = count_sandwiches(db_session, query=query)
    updated = 0
    done = False

    while done == False:
        sandwiches = fetch_sandwiches(
            db_session, query=query, offset=skip + updated, limit=limit
        )

        if len(sandwiches) == 0:
            done = True
            break

        # Get blocks and prices for calculating sandwich profit USD
        tokens: List[str] = []
        blockNumbers: List[int] = []
        for sandwich in sandwiches:
            tokenAddress = sandwich.frontrun_swap.token_in_address
            blockNumber = int(sandwich.block_number)
            if tokens.count(tokenAddress) < 1:
                tokens.append(tokenAddress)
            if blockNumbers.count(blockNumber) < 1:
                blockNumbers.append(blockNumber)
        prices = get_prices_map(db_session, tokens)
        blocks = get_blocks_map(db_session, blockNumbers)

        sandwichUpdates: List[Sandwich] = []
        for sandwich in sandwiches:
            try:
                tokenAddress = sandwich.frontrun_swap.token_in_address
                blockNumber = sandwich.block_number
                token = allTokens[tokenAddress] if tokenAddress in allTokens else None
                block = blocks[blockNumber] if blockNumber in blocks else None
                tokenPrices = prices[tokenAddress] if tokenAddress in prices else None
                sandwichNeedsUpdate = False

                profit = calculate_sandwich_profit(
                    sandwich.frontrun_swap, sandwich.backrun_swap, db_session
                )

                sandwich.profit_token_address = tokenAddress
                sandwich.profit_amount = profit
                if token is not None:
                    sandwich.profit_amount_decimal = float(
                        Decimal(sandwich.profit_amount) / Decimal(10 ** token.decimals)
                    )
                    sandwichNeedsUpdate = True
                if (
                    token is not None
                    and block is not None
                    and tokenPrices is not None
                    and sandwich.profit_amount_decimal is not None
                ):
                    price = get_closest_price(
                        block.block_timestamp.timestamp(), tokenPrices
                    )
                    profit_amount_usd = Decimal(
                        sandwich.profit_amount_decimal
                    ) * Decimal(price.usd_price)
                    sandwich.profit_amount_usd = float(round(profit_amount_usd, 2))
                    sandwichNeedsUpdate = True

                if sandwichNeedsUpdate:
                    sandwichUpdates.append(sandwich)
                    updated += 1
                else:
                    skip += 1

            except:
                skip += 1
                exc_type, exc_value, exc_traceback = sys.exc_info()
                lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
                logger.exception("".join("!! " + line for line in lines))

        if len(sandwichUpdates) > 0:
            logger.info(f"Write sandwiches {len(sandwichUpdates)}")
            update_sandwiches(db_session, sandwiches=sandwichUpdates)

        logger.info(f"Updated Sandwich Profits {updated+skip} / {count}")
