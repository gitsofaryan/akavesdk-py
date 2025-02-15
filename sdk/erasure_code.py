import reedsolo

class ErasureCode:
    """
    ErasureCode class for Reed-Solomon encoding and decoding.
    """

    def __init__(self, data_blocks: int, parity_blocks: int):
        """
        Initializes the ErasureCode instance.

        :param data_blocks: Number of data shards.
        :param parity_blocks: Number of parity shards.
        :raises ValueError: If data_blocks or parity_blocks are <= 0.
        """
        if data_blocks <= 0 or parity_blocks <= 0:
            raise ValueError("Data and parity shards must be > 0")

        self.data_blocks = data_blocks
        self.parity_blocks = parity_blocks
        self.total_blocks = data_blocks + parity_blocks

        # Initialize Reed-Solomon encoder/decoder
        self.rs = reedsolo.RSCodec(parity_blocks)

    def encode(self, data: bytes) -> list[bytes]:
        """
        Encodes input data using Reed-Solomon erasure coding.

        :param data: Raw data bytes.
        :return: List of encoded shards.
        """
        encoded_data = self.rs.encode(data)
        shard_size = len(encoded_data) // self.total_blocks
        return [encoded_data[i * shard_size : (i + 1) * shard_size] for i in range(self.total_blocks)]

    def extract_data(self, shards: list[bytes], original_data_size: int) -> bytes:
        """
        Extracts and reconstructs the original data from encoded shards.

        :param shards: List of data and parity shards.
        :param original_data_size: Size of the original data before encoding.
        :return: Reconstructed data bytes.
        :raises ValueError: If decoding fails.
        """
        try:
            reconstructed_data = self.rs.decode(b"".join(shards))
            return reconstructed_data[:original_data_size]
        except reedsolo.ReedSolomonError as e:
            raise ValueError(f"Failed to reconstruct data: {e}")
