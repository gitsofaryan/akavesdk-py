from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Dict, Any, List, Tuple

from eth_typing import Address, HexStr
from web3 import Web3
from web3.contract import Contract
from eth_account.signers.local import LocalAccount


class ListPolicyMetaData:
    ABI = [
        {"inputs": [], "name": "AlreadyWhitelisted", "type": "error"},
        {"inputs": [], "name": "InvalidAddress", "type": "error"},
        {"inputs": [], "name": "NotThePolicyOwner", "type": "error"},
        {"inputs": [], "name": "NotWhitelisted", "type": "error"},
        {
            "inputs": [{"internalType": "address", "name": "user", "type": "address"}],
            "name": "assignRole",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function",
        },
        {
            "inputs": [{"internalType": "address", "name": "_owner", "type": "address"}],
            "name": "initialize",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function",
        },
        {
            "inputs": [],
            "name": "owner",
            "outputs": [{"internalType": "address", "name": "", "type": "address"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [{"internalType": "address", "name": "user", "type": "address"}],
            "name": "revokeRole",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function",
        },
        {
            "inputs": [
                {"internalType": "address", "name": "user", "type": "address"},
                {"internalType": "bytes", "name": "data", "type": "bytes"},
            ],
            "name": "validateAccess",
            "outputs": [{"internalType": "bool", "name": "hasAccess", "type": "bool"}],
            "stateMutability": "view",
            "type": "function",
        },
    ]


class ListPolicyCaller:
    def __init__(self, contract: Contract):
        self.contract = contract

    def owner(self) -> Address:
        return self.contract.functions.owner().call()

    def validate_access(self, user: Address, data: bytes) -> bool:
        return self.contract.functions.validateAccess(user, data).call()


class ListPolicyTransactor:
    def __init__(self, contract: Contract, web3: Web3):
        self.contract = contract
        self.web3 = web3

    def assign_role(self, account: LocalAccount, user: Address, tx_params: Optional[Dict[str, Any]] = None) -> HexStr:
        params = {"from": account.address, "gasPrice": self.web3.eth.gas_price}
        if tx_params:
            params.update(tx_params)
        tx = self.contract.functions.assignRole(user).build_transaction(params)
        signed = account.sign_transaction(tx)
        tx_hash = self.web3.eth.send_raw_transaction(getattr(signed, "raw_transaction", getattr(signed, "rawTransaction")))
        return tx_hash.hex()

    def initialize(self, account: LocalAccount, owner: Address, tx_params: Optional[Dict[str, Any]] = None) -> HexStr:
        params = {"from": account.address, "gasPrice": self.web3.eth.gas_price}
        if tx_params:
            params.update(tx_params)
        tx = self.contract.functions.initialize(owner).build_transaction(params)
        signed = account.sign_transaction(tx)
        tx_hash = self.web3.eth.send_raw_transaction(getattr(signed, "raw_transaction", getattr(signed, "rawTransaction")))
        return tx_hash.hex()

    def revoke_role(self, account: LocalAccount, user: Address, tx_params: Optional[Dict[str, Any]] = None) -> HexStr:
        params = {"from": account.address, "gasPrice": self.web3.eth.gas_price}
        if tx_params:
            params.update(tx_params)
        tx = self.contract.functions.revokeRole(user).build_transaction(params)
        signed = account.sign_transaction(tx)
        tx_hash = self.web3.eth.send_raw_transaction(getattr(signed, "raw_transaction", getattr(signed, "rawTransaction")))
        return tx_hash.hex()


class ListPolicy:
    def __init__(self, w3: Web3, address: Address):
        self.web3 = w3
        self.contract = w3.eth.contract(address=address, abi=ListPolicyMetaData.ABI)
        self.caller = ListPolicyCaller(self.contract)
        self.transactor = ListPolicyTransactor(self.contract, w3)

    @property
    def address(self) -> Address:
        return self.contract.address


def new_list_policy(w3: Web3, address: Address) -> ListPolicy:
    return ListPolicy(w3, address)


