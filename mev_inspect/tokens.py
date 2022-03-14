import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

from web3 import HTTPProvider, Web3

from mev_inspect.crud.tokens import get_tokens, write_tokens
from mev_inspect.schemas.prices import TOKEN_ADDRESSES
from mev_inspect.schemas.tokens import Token

logger = logging.getLogger(__name__)

THIS_FILE_DIRECTORY = Path(__file__).parents[0]
ERC20_ABI_FILE_PATH = THIS_FILE_DIRECTORY / "abis" / "ERC20.json"
f = open(ERC20_ABI_FILE_PATH)
ERC20_ABI = json.load(f)

TOKENS_MAP: Dict[str, Token] = dict()


def fetch_tokens() -> List[Token]:
    base_provider = HTTPProvider(os.environ["RPC_URL"])
    w3 = Web3(base_provider)
    tokens = []
    for token_address in TOKEN_ADDRESSES:
        try:
            contract = w3.eth.contract(
                w3.toChecksumAddress(token_address), abi=ERC20_ABI
            )
            decimals = contract.functions.decimals().call()
            logger.info(f"Token & Decimals: {token_address} {decimals}")
            tokens.append(Token(token_address=token_address, decimals=decimals))
        except:
            logger.info("exeption thrown getting token decimals")
    return tokens


def save_token(db_session, token_address: str) -> None:
    base_provider = HTTPProvider(os.environ["RPC_URL"])
    w3 = Web3(base_provider)
    try:
        contract = w3.eth.contract(w3.toChecksumAddress(token_address), abi=ERC20_ABI)
        decimals = contract.functions.decimals().call()
        logger.info(f"Token & Decimals: {token_address} {decimals}")
        tokens = [Token(token_address=token_address, decimals=decimals)]
        write_tokens(db_session, tokens=tokens)
        update_tokens_map(tokens=tokens)
    except:
        logger.info("exeption thrown getting token decimals")


def get_token(db_session, token_address: str) -> Optional[Token]:
    get_tokens_map(db_session)
    if token_address in TOKENS_MAP:
        return TOKENS_MAP[token_address]
    save_token(db_session, token_address)
    if token_address in TOKENS_MAP:
        return TOKENS_MAP[token_address]
    return None


def get_tokens_map(db_session) -> Dict[str, Token]:
    if len(TOKENS_MAP) > 0:
        return TOKENS_MAP
    tokens = get_tokens(db_session)
    if tokens:
        update_tokens_map(tokens)
    return TOKENS_MAP


def update_tokens_map(tokens: List[Token] = []) -> Dict[str, Token]:
    if len(tokens) > 0:
        for token in tokens:
            TOKENS_MAP[token.token_address] = token
    return TOKENS_MAP
