from typing import List
import json
from pathlib import Path
import os

from web3 import Web3, HTTPProvider
from mev_inspect.schemas.prices import TOKEN_ADDRESSES
from mev_inspect.schemas.tokens import Token
import logging
logger = logging.getLogger(__name__)

THIS_FILE_DIRECTORY = Path(__file__).parents[0]
ERC20_ABI_FILE_PATH = THIS_FILE_DIRECTORY / "abis" / "ERC20.json"
f = open(ERC20_ABI_FILE_PATH)
ERC20_ABI = json.load(f)

def fetch_tokens() -> List[Token]:
    base_provider = HTTPProvider(os.environ["RPC_URL"])
    w3 = Web3(base_provider)
    tokens = []

    for token_address in TOKEN_ADDRESSES:
        try: 
          contract = w3.eth.contract(w3.toChecksumAddress(token_address), abi=ERC20_ABI)
          decimals = contract.functions.decimals().call()
          logger.info(f"Token & Decimals: {token_address} {decimals}")
          tokens.append(Token(token_address=token_address, decimals=decimals))
        except:
          logger.info('exeption thrown getting token decimals')
          
    return tokens

