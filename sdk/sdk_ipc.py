import time
import logging
from hashlib import sha256

from .sdk import MIN_BUCKET_NAME_LENGTH

class IPC:
    def __init__(self, client, conn, ipc, max_concurrency, block_part_size, use_connection_pool, encryption_key=None):
        self.client = client
        self.conn = conn
        self.ipc = ipc
        self.max_concurrency = max_concurrency
        self.block_part_size = block_part_size
        self.use_connection_pool = use_connection_pool
        self.encryption_key = encryption_key if encryption_key else b''

    def create_bucket(self, ctx, name):
        try:
            if len(name) < MIN_BUCKET_NAME_LENGTH:
                raise ValueError("Invalid bucket name")

            # Create the bucket using the IPC storage client
            tx = self.ipc.storage.create_bucket(self.ipc.auth, name)
            if tx is None:
                raise Exception("Failed to create bucket")

            # Wait for the transaction to be completed
            self.ipc.wait_for_tx(ctx, tx.hash())

            # Retrieve the bucket by name after the transaction is successful
            bucket = self.ipc.storage.get_bucket_by_name(self.ipc.auth.from_address, name)
            if bucket is None:
                raise Exception("Failed to retrieve the bucket")

            # Return the bucket creation result
            return {
                "name": sha256(bucket.id).hexdigest(),  # Assuming bucket.id is in a format that needs encoding like in Go's hex.EncodeToString
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(bucket.created_at))  # Assuming bucket.created_at is in Unix timestamp format
            }

        except Exception as err:
            logging.error(f"Error creating bucket: {str(err)}")
            raise
