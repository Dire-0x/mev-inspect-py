import logging
from typing import List
from uuid import uuid4

from sqlalchemy import orm

from mev_inspect.models.sandwiches import SandwichModel
from mev_inspect.models.swaps import SwapModel
from mev_inspect.schemas.sandwiches import Sandwich
from mev_inspect.schemas.swaps import Swap

from .shared import delete_by_block_range

logger = logging.getLogger(__name__)


def delete_sandwiches_for_blocks(
    db_session: orm.Session,
    after_block_number: int,
    before_block_number: int,
) -> None:
    delete_by_block_range(
        db_session,
        SandwichModel,
        after_block_number,
        before_block_number,
    )
    db_session.commit()


def write_sandwiches(
    db_session: orm.Session,
    sandwiches: List[Sandwich],
) -> None:
    sandwich_models = []
    sandwiched_swaps = []

    for sandwich in sandwiches:
        sandwich_id = str(uuid4())
        sandwich_models.append(
            SandwichModel(
                id=sandwich_id,
                block_number=sandwich.block_number,
                sandwicher_address=sandwich.sandwicher_address,
                frontrun_swap_transaction_hash=sandwich.frontrun_swap.transaction_hash,
                frontrun_swap_trace_address=sandwich.frontrun_swap.trace_address,
                backrun_swap_transaction_hash=sandwich.backrun_swap.transaction_hash,
                backrun_swap_trace_address=sandwich.backrun_swap.trace_address,
                profit_token_address=sandwich.profit_token_address,
                profit_amount=sandwich.profit_amount,
                profit_amount_decimal=sandwich.profit_amount_decimal,
                profit_amount_usd=sandwich.profit_amount_usd,
            )
        )

        for swap in sandwich.sandwiched_swaps:
            # logger.info(f"sandwiched_swap {swap}")
            sandwiched_swaps.append(
                {
                    "sandwich_id": sandwich_id,
                    "block_number": swap.block_number,
                    "transaction_hash": swap.transaction_hash,
                    "trace_address": swap.trace_address,
                }
            )

    if len(sandwich_models) > 0:
        db_session.bulk_save_objects(sandwich_models)
        db_session.execute(
            """
            INSERT INTO sandwiched_swaps
            (sandwich_id, block_number, transaction_hash, trace_address)
            VALUES
            (:sandwich_id, :block_number, :transaction_hash, :trace_address)
            """,
            params=sandwiched_swaps,
        )

        db_session.commit()


def update_sandwiches(
    db_session: orm.Session,
    sandwiches: List[Sandwich],
) -> None:
    if len(sandwiches) > 0:
        sandwich_models = []
        for sandwich in sandwiches:
            sandwich_models.append(sandwich.__dict__)
        db_session.bulk_update_mappings(SandwichModel, sandwich_models)
        db_session.commit()


def fetch_sandwiches(
    db_session: orm.Session, query: str, offset: int, limit: int
) -> List[Sandwich]:
    results: List[Sandwich] = []
    swaps: List[Swap] = []
    sandwiches: List[SandwichModel] = db_session.execute(
        f"SELECT * FROM sandwiches WHERE {query} ORDER BY profit_amount_usd DESC LIMIT {limit} OFFSET {offset}"
    ).all()
    swapHashes: List[str] = []
    if len(sandwiches):
        for sandwich in sandwiches:
            swapHashes.append(sandwich.frontrun_swap_transaction_hash)
            swapHashes.append(sandwich.backrun_swap_transaction_hash)

    if len(swapHashes):
        filter_string = f"IN {tuple(swapHashes)}"
        if len(swapHashes) == 1:
            filter_string = f"= '{swapHashes[0]}'"
        swapsResults: List[SwapModel] = db_session.execute(
            f"SELECT * FROM swaps WHERE transaction_hash {filter_string}"
        ).all()
        for swap in swapsResults:
            swaps.append(
                Swap(
                    abi_name=swap.abi_name,
                    transaction_eoa=swap.transaction_eoa,
                    transaction_hash=swap.transaction_hash,
                    transaction_position=swap.transaction_position,
                    block_number=swap.block_number,
                    trace_address=swap.trace_address,
                    contract_address=swap.contract_address,
                    from_address=swap.from_address,
                    to_address=swap.to_address,
                    token_in_address=swap.token_in_address,
                    token_in_amount=swap.token_in_amount,
                    token_out_address=swap.token_out_address,
                    token_out_amount=swap.token_out_amount,
                    protocol=swap.protocol,
                    error=swap.error,
                )
            )

    if len(sandwiches):
        for sandwich in sandwiches:
            frontrun_swap: Swap
            backrun_swap: Swap
            for s in swaps:
                if s.transaction_hash == sandwich.frontrun_swap_transaction_hash:
                    if "-".join(str(e) for e in s.trace_address) == "-".join(
                        str(e) for e in sandwich.frontrun_swap_trace_address
                    ):
                        frontrun_swap = s
                if s.transaction_hash == sandwich.backrun_swap_transaction_hash:
                    if "-".join(str(e) for e in s.trace_address) == "-".join(
                        str(e) for e in sandwich.backrun_swap_trace_address
                    ):
                        backrun_swap = s
            results.append(
                Sandwich(
                    id=sandwich.id,
                    block_number=sandwich.block_number,
                    sandwicher_address=sandwich.sandwicher_address,
                    frontrun_swap=frontrun_swap,
                    backrun_swap=backrun_swap,
                    sandwiched_swaps=[],
                    profit_token_address=sandwich.profit_token_address,
                    profit_amount=sandwich.profit_amount,
                    profit_amount_decimal=sandwich.profit_amount_decimal,
                    profit_amount_usd=sandwich.profit_amount_usd,
                )
            )
    return results


def count_sandwiches(
    db_session: orm.Session,
    query: str,
) -> int:
    sandwiches = db_session.execute(
        f"SELECT COUNT(*) AS count_1 FROM sandwiches WHERE {query}"
    ).scalar()
    return sandwiches
