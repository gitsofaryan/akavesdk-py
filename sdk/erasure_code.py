import reedsolo
from typing import Optional

class ErasureCode:
    """
    A wrapper around Reed-Solomon encoding, providing a more user-friendly interface.
    """
    def __init__(self, data_blocks: int, parity_blocks: int):
        if data_blocks <= 0 or parity_blocks <= 0:
            raise ValueError("Data and parity blocks must be greater than 0")

        self.data_blocks = data_blocks
        self.parity_blocks = parity_blocks
        self.enc = reedsolo.RSCodec(data_blocks + parity_blocks)

    def encode(self, data: bytes) -> bytes:
        """
        Encode the given data using Reed-Solomon encoding.
        """
        if len(data) != self.data_blocks:
            raise ValueError(f"Data length must be exactly {self.data_blocks} bytes.")

        return self.enc.encode(data)

    def decode(self, data: bytes) -> Optional[bytes]:
        """
        Decode the given data using Reed-Solomon decoding.
        Returns None if unable to recover the data.
        """
        try:
            return self.enc.decode(data)
        except reedsolo.ReedSolomonError:
            return None

