from typing import List, Tuple, Optional
from eth_typing import HexAddress, HexStr
from web3 import Web3
from web3.contract import Contract
from eth_account import Account
import json

class StorageContract:
    """Python bindings for the Storage smart contract."""
    
    def __init__(self, web3: Web3, contract_address: HexAddress):
        """Initialize the Storage contract interface.
        
        Args:
            web3: Web3 instance
            contract_address: Address of the deployed Storage contract
        """
        self.web3 = web3
        self.contract_address = contract_address
        
        # Contract ABI from the Go bindings
        self.abi = [
            {
                "inputs": [
                    {
                        "internalType": "address",
                        "name": "_accessManager",
                        "type": "address"
                    }
                ],
                "stateMutability": "nonpayable",
                "type": "constructor"
            },
            {
                "inputs": [],
                "name": "accessManager",
                "outputs": [
                    {
                        "internalType": "address",
                        "name": "",
                        "type": "address"
                    }
                ],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [
                    {
                        "internalType": "string",
                        "name": "bucketName",
                        "type": "string"
                    }
                ],
                "name": "createBucket",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [
                    {
                        "internalType": "string",
                        "name": "bucketName",
                        "type": "string"
                    },
                    {
                        "internalType": "string",
                        "name": "fileName",
                        "type": "string"
                    },
                    {
                        "internalType": "bytes32",
                        "name": "fileId",
                        "type": "bytes32"
                    },
                    {
                        "internalType": "uint256",
                        "name": "size",
                        "type": "uint256"
                    }
                ],
                "name": "createFile",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [
                    {
                        "internalType": "string",
                        "name": "bucketName",
                        "type": "string"
                    }
                ],
                "name": "deleteBucket",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [
                    {
                        "internalType": "string",
                        "name": "bucketName",
                        "type": "string"
                    },
                    {
                        "internalType": "string",
                        "name": "fileName",
                        "type": "string"
                    }
                ],
                "name": "deleteFile",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [
                    {
                        "internalType": "string",
                        "name": "bucketName",
                        "type": "string"
                    }
                ],
                "name": "getBucket",
                "outputs": [
                    {
                        "components": [
                            {
                                "internalType": "string",
                                "name": "name",
                                "type": "string"
                            },
                            {
                                "internalType": "uint256",
                                "name": "createdAt",
                                "type": "uint256"
                            },
                            {
                                "internalType": "address",
                                "name": "owner",
                                "type": "address"
                            }
                        ],
                        "internalType": "struct Storage.Bucket",
                        "name": "",
                        "type": "tuple"
                    }
                ],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [
                    {
                        "internalType": "string",
                        "name": "bucketName",
                        "type": "string"
                    },
                    {
                        "internalType": "string",
                        "name": "fileName",
                        "type": "string"
                    }
                ],
                "name": "getFile",
                "outputs": [
                    {
                        "components": [
                            {
                                "internalType": "string",
                                "name": "name",
                                "type": "string"
                            },
                            {
                                "internalType": "bytes32",
                                "name": "id",
                                "type": "bytes32"
                            },
                            {
                                "internalType": "uint256",
                                "name": "size",
                                "type": "uint256"
                            },
                            {
                                "internalType": "uint256",
                                "name": "createdAt",
                                "type": "uint256"
                            }
                        ],
                        "internalType": "struct Storage.File",
                        "name": "",
                        "type": "tuple"
                    }
                ],
                "stateMutability": "view",
                "type": "function"
            }
        ]
        
        self.contract = web3.eth.contract(address=contract_address, abi=self.abi)

    def get_access_manager(self) -> HexAddress:
        """Gets the address of the associated access manager contract.
        
        Returns:
            Address of the access manager contract
        """
        return self.contract.functions.accessManager().call()

    def create_bucket(self, bucket_name: str, from_address: HexAddress, private_key: str, gas_limit: int = None) -> None:
        """Creates a new bucket.
        
        Args:
            bucket_name: Name of the bucket to create
            from_address: Address creating the bucket
            private_key: Private key for signing the transaction
            gas_limit: Optional gas limit for the transaction. If not provided, will use default.
        """
        # Build transaction
        tx_params = {
            'from': from_address,
            'gasPrice': self.web3.eth.gas_price,
            'nonce': self.web3.eth.get_transaction_count(from_address)
        }
        
        if gas_limit:
            tx_params['gas'] = gas_limit
        else:
            tx_params['gas'] = 500000  # Default gas limit
            
        tx = self.contract.functions.createBucket(bucket_name).build_transaction(tx_params)
        
        # Sign transaction
        signed_tx = Account.sign_transaction(tx, private_key)
        
        # Send raw transaction
        tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        
        # Wait for receipt
        receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
        if receipt.status != 1:
            # Get revert reason if possible
            try:
                self.contract.functions.createBucket(bucket_name).call({
                    'from': from_address
                })
            except Exception as e:
                raise Exception(f"Transaction reverted: {str(e)}")
            raise Exception(f"Transaction failed. Receipt: {receipt}")

    def create_file(self, bucket_name: str, file_name: str, file_id: bytes, size: int, from_address: HexAddress, private_key: str) -> None:
        """Creates a new file entry.
        
        Args:
            bucket_name: Name of the bucket containing the file
            file_name: Name of the file
            file_id: Unique ID of the file
            size: Size of the file in bytes
            from_address: Address creating the file
            private_key: Private key for signing the transaction
        """
        # Build transaction
        tx = self.contract.functions.createFile(bucket_name, file_name, file_id, size).build_transaction({
            'from': from_address,
            'gas': 500000,  # Gas limit
            'gasPrice': self.web3.eth.gas_price,
            'nonce': self.web3.eth.get_transaction_count(from_address)
        })
        
        # Sign transaction
        signed_tx = Account.sign_transaction(tx, private_key)
        
        # Send raw transaction
        tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        
        # Wait for receipt
        receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
        if receipt.status != 1:
            raise Exception("Transaction failed")

    def commit_file(self, bucket_name: str, file_name: str, size: int, root_cid: bytes, from_address: HexAddress, private_key: str) -> None:
        """Updates the file metadata after upload (size, root CID).
        
        Args:
            bucket_name: Name of the bucket containing the file
            file_name: Name of the file
            size: Final size of the file in bytes
            root_cid: Root CID of the uploaded file
            from_address: Address committing the file
            private_key: Private key for signing the transaction
        """
        # Assume a contract function like 'commitFile' or 'updateFileMetadata' exists
        # Adding 'commitFile' based on Go SDK patterns
        function_name = 'commitFile' # Adjust if contract ABI uses a different name
        
        try:
            contract_function = getattr(self.contract.functions, function_name)
        except AttributeError:
            raise NotImplementedError(f"Contract function '{function_name}' not found in ABI")
            
        # Build transaction
        tx = contract_function(bucket_name, file_name, size, root_cid).build_transaction({
            'from': from_address,
            'gas': 500000,  # Gas limit (adjust as needed)
            'gasPrice': self.web3.eth.gas_price,
            'nonce': self.web3.eth.get_transaction_count(from_address)
        })
        
        # Sign transaction
        signed_tx = Account.sign_transaction(tx, private_key)
        
        # Send raw transaction
        tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        
        # Wait for receipt
        receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
        if receipt.status != 1:
            raise Exception(f"Transaction failed for {function_name}")

    def delete_bucket(self, bucket_name: str, from_address: HexAddress, private_key: str) -> HexStr:
        """Deletes a bucket.
        
        Args:
            bucket_name: Name of the bucket to delete
            from_address: Address deleting the bucket
            private_key: Private key for signing the transaction
            
        Returns:
            Transaction hash of the delete operation
            
        Raises:
            Exception: If the transaction fails or is reverted
        """
        # Build transaction
        tx_params = {
            'from': from_address,
            'gas': 500000,  # Gas limit
            'gasPrice': self.web3.eth.gas_price,
            'nonce': self.web3.eth.get_transaction_count(from_address)
        }
            
        tx = self.contract.functions.deleteBucket(bucket_name).build_transaction(tx_params)
        
        # Sign transaction
        signed_tx = Account.sign_transaction(tx, private_key)
        
        # Send raw transaction
        tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        
        return tx_hash

    def delete_file(self, bucket_name: str, file_name: str, from_address: HexAddress, private_key: str) -> None:
        """Deletes a file.
        
        Args:
            bucket_name: Name of the bucket containing the file
            file_name: Name of the file to delete
            from_address: Address deleting the file
            private_key: Private key for signing the transaction
        """
        # Build transaction
        tx = self.contract.functions.deleteFile(bucket_name, file_name).build_transaction({
            'from': from_address,
            'gas': 500000,  # Gas limit
            'gasPrice': self.web3.eth.gas_price,
            'nonce': self.web3.eth.get_transaction_count(from_address)
        })
        
        # Sign transaction
        signed_tx = Account.sign_transaction(tx, private_key)
        
        # Send raw transaction
        tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        
        # Wait for receipt
        receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
        if receipt.status != 1:
            raise Exception("Transaction failed")

    def get_bucket(self, bucket_name: str) -> Tuple[str, int, HexAddress]:
        """Gets bucket information.
        
        Args:
            bucket_name: Name of the bucket
            
        Returns:
            Tuple containing (bucket_name, created_at_timestamp, owner_address)
        """
        return self.contract.functions.getBucket(bucket_name).call()

    def get_file(self, bucket_name: str, file_name: str) -> Tuple[str, bytes, int, int]:
        """Gets file information.
        
        Args:
            bucket_name: Name of the bucket containing the file
            file_name: Name of the file
            
        Returns:
            Tuple containing (file_name, file_id, size, created_at_timestamp)
        """
        return self.contract.functions.getFile(bucket_name, file_name).call()
