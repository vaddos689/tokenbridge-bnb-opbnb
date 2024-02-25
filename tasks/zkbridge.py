import asyncio
from client import Client
from loguru import logger
from models import TokenAmount
from settings import BRIDGE_BNB_AMOUNT, BSC_GWEI, WAIT_OPBNB_DEPOSIT
from utils import read_json


class ZkBridge:
    def __init__(self, client: Client):
        self.client = client
        self.bridge_contract_address = self.client.w3.to_checksum_address('0x51187757342914E7d94FFFD95cCCa4f440FE0E06')
        self.bridge_abi = read_json('abis/bridge_abi.json')

    async def get_balance(self) -> TokenAmount:
        balance_wei = await self.client.get_balance()
        return TokenAmount(amount=balance_wei, wei=True)

    async def estimate_fee(self):
        contract = self.client.w3.eth.contract(
            address=self.bridge_contract_address,
            abi=self.bridge_abi
        )

        bridge_fee = await contract.functions.estimateFee(10, 23, self.client.w3.to_wei(BRIDGE_BNB_AMOUNT, 'ether')).call()
        return bridge_fee

    async def wait_opbnb(self):
        zkbridge = ZkBridge(Client(rpc='https://opbnb-mainnet-rpc.bnbchain.org', private_key=self.client.wallet.private_key))
        try:
            balance = await zkbridge.get_balance()
            if balance.Ether == BRIDGE_BNB_AMOUNT:
                logger.success(f'[{self.client.wallet.short_address}] Opbnb successful bridge')
                return True
            else:
                logger.debug(f'[{self.client.wallet.short_address}] Waiting Opbnb...')
                await asyncio.sleep(60)
                await self.wait_opbnb()
        except Exception as ex:
            logger.error(f'[{self.client.wallet.short_address}] Error with get opbnb balance')

    async def main(self):
        balance: TokenAmount = await self.get_balance()
        logger.info(f'[{self.client.wallet.short_address}] $BNB balance: {balance.Ether} | Bridge amount: {BRIDGE_BNB_AMOUNT}')
        bridge_fee = await self.estimate_fee()
        tx_params = await self.client.get_tx_params(bridge_fee=bridge_fee, amount=BRIDGE_BNB_AMOUNT, gwei=BSC_GWEI)

        contract = self.client.w3.eth.contract(
            address=self.bridge_contract_address,
            abi=self.bridge_abi
        )

        tx = await contract.functions.transferETH(23, self.client.w3.to_wei(BRIDGE_BNB_AMOUNT, 'ether'), self.client.wallet.address).build_transaction(tx_params)
        signed_txn = self.client.w3.eth.account.sign_transaction(tx, self.client.wallet.private_key)
        res = await self.client.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        await self.client.verif_tx(res)
        logger.info(f'[{self.client.wallet.short_address}] Wait $BNB Opbnb')
        if WAIT_OPBNB_DEPOSIT:
            await self.wait_opbnb()


async def start_bridge(wallet: str):
    zkbridge = ZkBridge(Client(rpc='https://rpc.ankr.com/bsc', private_key=wallet))
    await zkbridge.main()
