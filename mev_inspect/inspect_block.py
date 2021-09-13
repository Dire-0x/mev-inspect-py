from web3 import Web3

from mev_inspect.arbitrages import get_arbitrages
from mev_inspect.block import create_from_block_number
from mev_inspect.classifiers.trace import TraceClassifier
from mev_inspect.crud.arbitrages import (
    delete_arbitrages_for_block,
    write_arbitrages,
)
from mev_inspect.crud.classified_traces import (
    delete_classified_traces_for_block,
    write_classified_traces,
)
from mev_inspect.crud.miner_payments import (
    delete_miner_payments_for_block,
    write_miner_payments,
)
from mev_inspect.crud.swaps import delete_swaps_for_block, write_swaps
from mev_inspect.db import get_session
from mev_inspect.miner_payments import get_miner_payments
from mev_inspect.swaps import get_swaps


def inspect_block(
    db_session,
    base_provider,
    w3: Web3,
    block_number: int,
    should_cache: bool,
    should_write_classified_traces: bool = True,
    should_write_swaps: bool = True,
    should_write_arbitrages: bool = True,
    should_write_miner_payments: bool = True,
):
    block = create_from_block_number(base_provider, w3, block_number, should_cache)

    print(f"Total traces: {len(block.traces)}")

    total_transactions = len(
        set(t.transaction_hash for t in block.traces if t.transaction_hash is not None)
    )
    print(f"Total transactions: {total_transactions}")

    trace_clasifier = TraceClassifier()
    classified_traces = trace_clasifier.classify(block.traces)
    print(f"Returned {len(classified_traces)} classified traces")

    db_session = get_session()

    if should_write_classified_traces:
        delete_classified_traces_for_block(db_session, block_number)
        write_classified_traces(db_session, classified_traces)

    swaps = get_swaps(classified_traces)
    print(f"Found {len(swaps)} swaps")

    if should_write_swaps:
        delete_swaps_for_block(db_session, block_number)
        write_swaps(db_session, swaps)

    arbitrages = get_arbitrages(swaps)
    print(f"Found {len(arbitrages)} arbitrages")

    if should_write_arbitrages:
        delete_arbitrages_for_block(db_session, block_number)
        write_arbitrages(db_session, arbitrages)

    miner_payments = get_miner_payments(
        block.miner, block.base_fee_per_gas, classified_traces, block.receipts
    )

    if should_write_miner_payments:
        delete_miner_payments_for_block(db_session, block_number)
        write_miner_payments(db_session, miner_payments)