from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Dict, Any, List, Tuple

from eth_typing import Address, HexStr
from web3 import Web3
from web3.contract import Contract
from web3.types import LogReceipt
from eth_account.signers.local import LocalAccount


class PolicyFactoryMetaData:
    ABI = [
        {
            "inputs": [
                {"internalType": "address", "name": "_basePolicyImplementation", "type": "address"}
            ],
            "stateMutability": "nonpayable",
            "type": "constructor",
        },
        {"inputs": [], "name": "FailedDeployment", "type": "error"},
        {
            "inputs": [
                {"internalType": "uint256", "name": "balance", "type": "uint256"},
                {"internalType": "uint256", "name": "needed", "type": "uint256"},
            ],
            "name": "InsufficientBalance",
            "type": "error",
        },
        {
            "anonymous": False,
            "inputs": [
                {"indexed": True, "internalType": "address", "name": "owner", "type": "address"},
                {
                    "indexed": True,
                    "internalType": "address",
                    "name": "policyInstance",
                    "type": "address",
                },
            ],
            "name": "PolicyDeployed",
            "type": "event",
        },
        {
            "inputs": [],
            "name": "basePolicyImplementation",
            "outputs": [{"internalType": "address", "name": "", "type": "address"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [{"internalType": "bytes", "name": "initData", "type": "bytes"}],
            "name": "deployPolicy",
            "outputs": [
                {"internalType": "address", "name": "policyInstance", "type": "address"}
            ],
            "stateMutability": "nonpayable",
            "type": "function",
        },
    ]


class PolicyFactoryCaller:
    def __init__(self, contract: Contract):
        self.contract = contract

    def base_policy_implementation(self) -> Address:
        return self.contract.functions.basePolicyImplementation().call()


class PolicyFactoryTransactor:
    def __init__(self, contract: Contract, web3: Web3):
        self.contract = contract
        self.web3 = web3

    def deploy_policy(self, account: LocalAccount, init_data: bytes, tx_params: Optional[Dict[str, Any]] = None) -> HexStr:
        params = {"from": account.address, "gasPrice": self.web3.eth.gas_price}
        if tx_params:
            params.update(tx_params)
        tx = self.contract.functions.deployPolicy(init_data).build_transaction(params)
        signed = account.sign_transaction(tx)
        tx_hash = self.web3.eth.send_raw_transaction(getattr(signed, "raw_transaction", getattr(signed, "rawTransaction")))
        return tx_hash.hex()


class PolicyFactoryFilterer:
    def __init__(self, contract: Contract, web3: Web3):
        self.contract = contract
        self.web3 = web3

    def parse_policy_deployed(self, log: LogReceipt) -> Tuple[Address, Address]:
        event = self.contract.events.PolicyDeployed().processLog(log)
        owner = event["args"]["owner"]
        instance = event["args"]["policyInstance"]
        return owner, instance


class PolicyFactory:
    def __init__(self, w3: Web3, address: Address):
        self.web3 = w3
        self.contract = w3.eth.contract(address=address, abi=PolicyFactoryMetaData.ABI)
        self.caller = PolicyFactoryCaller(self.contract)
        self.transactor = PolicyFactoryTransactor(self.contract, w3)
        self.filterer = PolicyFactoryFilterer(self.contract, w3)

    @property
    def address(self) -> Address:
        return self.contract.address


def new_policy_factory(w3: Web3, address: Address) -> PolicyFactory:
    return PolicyFactory(w3, address)


