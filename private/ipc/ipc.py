from __future__ import annotations

import secrets
from dataclasses import dataclass
from typing import Dict, List, Any

from eth_utils import keccak, to_bytes, to_checksum_address

from ..eip712 import Domain as EIP712Domain, TypedData as EIP712TypedData, sign as eip712_sign


@dataclass
class StorageData:
    chunkCID: bytes
    blockCID: bytes
    chunkIndex: int
    blockIndex: int
    nodeId: bytes
    nonce: int
    deadline: int
    bucketId: bytes

    def to_message_dict(self) -> Dict[str, Any]:
        return {
            "chunkCID": self.chunkCID,
            "blockCID": self.blockCID,
            "chunkIndex": self.chunkIndex,
            "blockIndex": self.blockIndex,
            "nodeId": self.nodeId,
            "nonce": self.nonce,
            "deadline": self.deadline,
            "bucketId": self.bucketId,
        }


def generate_nonce() -> int:
    return int.from_bytes(secrets.token_bytes(32), byteorder="big")


def calculate_file_id(bucket_id: bytes, name: str) -> bytes:
    if not isinstance(bucket_id, (bytes, bytearray)):
        raise TypeError("bucket_id must be bytes32")
    return keccak(bucket_id + name.encode())


def calculate_bucket_id(bucket_name: str, owner_address: str) -> bytes:
    addr = owner_address.lower()
    if addr.startswith("0x"):
        addr = addr[2:]
    if len(addr) != 40:
        raise ValueError("owner_address must be a 20-byte hex string")
    address_bytes = bytes.fromhex(addr)
    return keccak(bucket_name.encode() + address_bytes)


def sign_block(private_key_hex: str, storage_address: str, chain_id: int, data: StorageData) -> bytes:
    key_hex = private_key_hex.lower()
    if key_hex.startswith("0x"):
        key_hex = key_hex[2:]
    private_key_bytes = bytes.fromhex(key_hex)

    checksum_addr = to_checksum_address(storage_address)

    domain = EIP712Domain(
        name="Storage",
        version="1",
        chain_id=chain_id,
        verifying_contract=checksum_addr,
    )

    storage_data_types: Dict[str, List[EIP712TypedData]] = {
        "StorageData": [
            EIP712TypedData("chunkCID", "bytes"),
            EIP712TypedData("blockCID", "bytes32"),
            EIP712TypedData("chunkIndex", "uint256"),
            EIP712TypedData("blockIndex", "uint8"),
            EIP712TypedData("nodeId", "bytes32"),
            EIP712TypedData("nonce", "uint256"),
            EIP712TypedData("deadline", "uint256"),
            EIP712TypedData("bucketId", "bytes32"),
        ]
    }

    message = data.to_message_dict()

    return eip712_sign(private_key_bytes, domain, message, storage_data_types)


