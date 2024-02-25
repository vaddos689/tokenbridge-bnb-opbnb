import asyncio
import random
from better_web3 import Wallet
from loguru import logger
from web3 import Web3
from web3.eth import AsyncEth
from models import TokenAmount


class Client:
    def __init__(self, rpc: str, private_key: str):
        self.rpc = rpc
        self.w3 = Web3(
            provider=Web3.AsyncHTTPProvider(
                endpoint_uri=self.rpc,
            ),
            modules={'eth': (AsyncEth,)},
            middlewares=[]
        )
        self.account = self.w3.eth.account.from_key(private_key=private_key)
        self.wallet = Wallet(self.account)

    async def verif_tx(self, tx_hash) -> bool:
        try:
            data = await self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=200)
            if 'status' in data and data['status'] == 1:
                logger.success(f'{self.wallet.short_address} | transaction was successful: {tx_hash.hex()}')
                return True
            else:
                logger.error(f'[{self.wallet.short_address}] | transaction failed {data["transactionHash"].hex()}')
                return False
        except Exception as err:
            logger.error(f'{self.wallet.short_address} | unexpected error in <verif_tx> function: {err}')
            return False

    async def get_tx_params(self, bridge_fee, amount, gwei):
        nonce = await self.w3.eth.get_transaction_count(self.wallet.address)
        tx_params = {
            'from': self.wallet.address,
            'nonce': nonce,
            'value': self.w3.to_wei(amount, 'ether') + bridge_fee,
            'gasPrice': self.w3.to_wei(gwei, 'gwei')
        }

        return tx_params

    async def get_balance(self, address: str | None = None):
        if not address:
            address = self.account.address
        return await self.w3.eth.get_balance(account=address)

