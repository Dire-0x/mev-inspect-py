from typing import List, Optional
from decimal import Decimal
from mev_inspect.models.sandwiches import SandwichModel
from mev_inspect.schemas.sandwiches import Sandwich
from mev_inspect.schemas.swaps import Swap
from mev_inspect.crud.sandwiches import fetch_sandwiches, count_sandwiches, update_sandwiches
from mev_inspect.block import get_blocks_map
from mev_inspect.prices import get_prices_map, get_closest_price
from mev_inspect.tokens import get_tokens_map
import sys
import traceback
import logging
logger = logging.getLogger(__name__)

UNISWAP_V2_ROUTER = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"
UNISWAP_V3_ROUTER = "0x68b3465833fb72a70ecdf485e0e4c7bd8665fc45"


def get_sandwiches(swaps: List[Swap]) -> List[Sandwich]:
    ordered_swaps = list(
        sorted(
            swaps,
            key=lambda swap: (swap.transaction_position, swap.trace_address),
        )
    )

    sandwiches: List[Sandwich] = []

    for index, swap in enumerate(ordered_swaps):
        rest_swaps = ordered_swaps[index + 1 :]
        sandwich = _get_sandwich_starting_with_swap(swap, rest_swaps)

        if sandwich is not None:
            sandwiches.append(sandwich)

    return sandwiches


def _get_sandwich_starting_with_swap(
    front_swap: Swap,
    rest_swaps: List[Swap],
) -> Optional[Sandwich]:
    sandwicher_address = front_swap.to_address
    sandwiched_swaps = []

    if sandwicher_address in [UNISWAP_V2_ROUTER, UNISWAP_V3_ROUTER]:
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
                    return Sandwich(
                        block_number=front_swap.block_number,
                        sandwicher_address=sandwicher_address,
                        frontrun_swap=front_swap,
                        backrun_swap=other_swap,
                        sandwiched_swaps=sandwiched_swaps,
                        profit_token_address=front_swap.token_in_address,
                        profit_amount=other_swap.token_out_amount
                        - front_swap.token_in_amount,
                    )

    return None

def update_sandwich_profit_usd(db_session, query:str = 'profit_amount_usd IS NULL') -> None:
    logger.info("start update sandwich profit usd")

    allTokens = get_tokens_map(db_session)

    limit = 100
    skip = 0
    count = count_sandwiches(db_session, query=query)
    updated = 0
    done = False

    while done == False:
        sandwiches = fetch_sandwiches(
            db_session,
            query=query,
            offset=skip,
            limit=limit
        )
        if len(sandwiches) == 0:
            done = True
            break

        # Get blocks and prices for calculating sandwich profit USD
        tokens: List[str] = []
        blockNumbers: List[int] = []
        for sandwich in sandwiches:
            tokenAddress = sandwich.profit_token_address
            blockNumber = int(sandwich.block_number)
            if tokens.count(tokenAddress) < 1:
                tokens.append(tokenAddress)
            if blockNumbers.count(blockNumber) < 1:
                blockNumbers.append(blockNumber)
        prices = get_prices_map(db_session, tokens)
        blocks = get_blocks_map(db_session, blockNumbers)

        sandwichUpdates: List[SandwichModel] = []
        for sandwich in sandwiches:
            try:
                tokenAddress = sandwich.profit_token_address
                blockNumber = int(sandwich.block_number)
                token = allTokens[tokenAddress] if tokenAddress in allTokens else None
                block = blocks[blockNumber] if blockNumber in blocks else None
                tokenPrices = prices[tokenAddress] if tokenAddress in prices else None
                if token is not None and block is not None and tokenPrices is not None:
                    price = get_closest_price(block.block_timestamp, tokenPrices)
                    model = SandwichModel(**sandwich)
                    model.profit_amount_decimal = round(sandwich.profit_amount / Decimal(10 ** token.decimals), 6)
                    model.profit_amount_usd = round(model.profit_amount_decimal * price.usd_price, 6)
                    sandwichUpdates.append(model)
                    updated+=1
                else:
                    skip+=1
            except:
                skip+=1
                exc_type, exc_value, exc_traceback = sys.exc_info()
                lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
                logger.exception(''.join('!! ' + line for line in lines))

        if len(sandwichUpdates) > 0:
            update_sandwiches(db_session, sandwiches=sandwichUpdates)

        logger.info(f"Updated Sandwich Profits {updated+skip} / {count}")


