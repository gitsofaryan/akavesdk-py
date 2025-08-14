from typing import Optional, Dict, Any, List
from web3 import Web3
from web3.contract import Contract
from eth_typing import Address, HexStr
from eth_account.signers.local import LocalAccount


class SinkMetaData:
    ABI = [{"stateMutability": "nonpayable", "type": "fallback"}]
    BIN = "0x6080604052348015600e575f5ffd5b50604680601a5f395ff3fe6080604052348015600e575f5ffd5b00fea2646970667358221220f43799cb6e28e32500f5eb3784cc07778d26ab2be04f4ee9fd27d581ad2138f464736f6c634300081c0033"


class SinkCaller:
    
    def __init__(self, contract: Contract):
        self.contract = contract


class SinkTransactor:
    
    def __init__(self, contract: Contract):
        self.contract = contract
    
    def fallback(self, calldata: bytes, tx_params: Optional[Dict[str, Any]] = None) -> HexStr:
        if tx_params is None:
            tx_params = {}
        
        return self.contract.fallback.transact(tx_params, calldata)


class SinkFilterer:    
    def __init__(self, contract: Contract):
        self.contract = contract


class Sink:    
    def __init__(self, contract: Contract):
        self.contract = contract
        self.caller = SinkCaller(contract)
        self.transactor = SinkTransactor(contract)
        self.filterer = SinkFilterer(contract)
    
    @property
    def address(self) -> Address:
        return self.contract.address
    
    def fallback(self, calldata: bytes, tx_params: Optional[Dict[str, Any]] = None) -> HexStr:
        return self.transactor.fallback(calldata, tx_params)


class SinkSession:    
    def __init__(self, contract: Sink, default_account: Optional[LocalAccount] = None, 
                 default_tx_params: Optional[Dict[str, Any]] = None):
        self.contract = contract
        self.default_account = default_account
        self.default_tx_params = default_tx_params or {}
    
    def fallback(self, calldata: bytes, tx_params: Optional[Dict[str, Any]] = None) -> HexStr:
        merged_params = {**self.default_tx_params, **(tx_params or {})}
        if self.default_account:
            merged_params['from'] = self.default_account.address
        
        return self.contract.fallback(calldata, merged_params)


def deploy_sink(w3: Web3, account: LocalAccount, 
                constructor_args: Optional[List[Any]] = None,
                tx_params: Optional[Dict[str, Any]] = None) -> tuple[Address, HexStr, Sink]:
    if constructor_args is None:
        constructor_args = []
    
    if tx_params is None:
        tx_params = {}
    
    tx_params['from'] = account.address
    
    contract = w3.eth.contract(abi=SinkMetaData.ABI, bytecode=SinkMetaData.BIN)
    
    constructor_tx = contract.constructor(*constructor_args).build_transaction(tx_params)
    
    signed_tx = account.sign_transaction(constructor_tx)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    
    deployed_contract = w3.eth.contract(
        address=tx_receipt.contractAddress,
        abi=SinkMetaData.ABI
    )
    
    return tx_receipt.contractAddress, tx_hash, Sink(deployed_contract)


def new_sink(w3: Web3, address: Address) -> Sink:
    contract = w3.eth.contract(address=address, abi=SinkMetaData.ABI)
    return Sink(contract)


def new_sink_caller(w3: Web3, address: Address) -> SinkCaller:
    contract = w3.eth.contract(address=address, abi=SinkMetaData.ABI)
    return SinkCaller(contract)


def new_sink_transactor(w3: Web3, address: Address) -> SinkTransactor:
    contract = w3.eth.contract(address=address, abi=SinkMetaData.ABI)
    return SinkTransactor(contract)


def new_sink_filterer(w3: Web3, address: Address) -> SinkFilterer:
    contract = w3.eth.contract(address=address, abi=SinkMetaData.ABI)
    return SinkFilterer(contract)
