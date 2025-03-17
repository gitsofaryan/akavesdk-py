import zfec

class ErasureCode:
    def __init__(self, data_blocks: int, parity_blocks: int):
        if data_blocks <= 0 or parity_blocks <= 0:
            raise ValueError("Data and parity shards must be > 0")
        self.data_blocks = data_blocks
        self.parity_blocks = parity_blocks
        self.total_blocks = data_blocks + parity_blocks
        self.fec = zfec.Encoder(self.data_blocks, self.total_blocks)

    def encode(self, data: bytes) -> list:
        # Calculate shard size with padding
        shard_size = (len(data) + self.data_blocks - 1) // self.data_blocks
        padded_data = data.ljust(shard_size * self.data_blocks, b'\0')
        
        # Split into data shards
        data_shards = [
            padded_data[i*shard_size : (i+1)*shard_size]
            for i in range(self.data_blocks)
        ]
        
        # Encode to get parity shards
        return self.fec.encode(data_shards)

    def decode(self, shards, shard_indices):
        decoder = zfec.Decoder(self.data_blocks, self.total_blocks)
        return decoder.decode(shards, shard_indices)

    def extract_data(self, blocks, original_data_size):
        # Identify available shards and their indices
        present_shards = []
        present_indices = []
        for idx, shard in enumerate(blocks):
            if shard is not None and shard != b'':
                present_shards.append(shard)
                present_indices.append(idx)

        # Verify enough shards are available
        if len(present_shards) < self.data_blocks:
            raise RuntimeError(f"Need {self.data_blocks} shards, got {len(present_shards)}")

        # Decode using ANY k shards (data or parity)
        decoded_shards = self.decode(present_shards[:self.data_blocks], 
                                  present_indices[:self.data_blocks])

        # Reconstruct original data with proper padding
        combined = b''.join(decoded_shards)[:original_data_size]
        return combined