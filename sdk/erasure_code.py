import math
from reedsolo import RSCodec, ReedSolomonError
from itertools import combinations

def missing_shards_idx(n, k):
    return [list(combo) for combo in combinations(range(n), k)]

def split_into_blocks(encoded: bytes, shard_size: int):
    blocks = []
    for offset in range(0, len(encoded), shard_size):
        block = encoded[offset: offset + shard_size]
        if len(block) < shard_size:
            block = block.ljust(shard_size, b'\x00')
        blocks.append(block)
    return blocks

class ErasureCode:
    def __init__(self, data_blocks: int, parity_blocks: int):
        if data_blocks <= 0 or parity_blocks <= 0:
            raise ValueError("Data and parity shards must be > 0")
        self.data_blocks = data_blocks
        self.parity_blocks = parity_blocks
        self.total_shards = data_blocks + parity_blocks

    @classmethod
    def new(cls, data_blocks: int, parity_blocks: int):
        return cls(data_blocks, parity_blocks)

    def encode(self, data: bytes) -> bytes:
        total_size = len(data)
        shard_size = math.ceil(total_size / self.data_blocks)
        padded_data = data.ljust(self.data_blocks * shard_size, b'\x00')
        
        # Split into data shards
        shards = [bytearray(padded_data[i * shard_size : (i + 1) * shard_size]) 
                  for i in range(self.data_blocks)]
        
        # Initialize parity shards
        parity_shards = [bytearray(shard_size) for _ in range(self.parity_blocks)]
        
        # Initialize RS codec for per-byte encoding
        # nsym = number of parity symbols (bytes) per message
        rsc = RSCodec(self.parity_blocks)
        
        # Stripe-based encoding:
        # For each byte index `j` in the shards (0 to shard_size-1):
        #   Take the j-th byte from each data shard -> form a message of `data_blocks` bytes.
        #   Encode it. Result is `data_blocks` original bytes + `parity_blocks` parity bytes.
        #   Store the parity bytes in the respective parity shards at index `j`.
        
        for j in range(shard_size):
            message = bytearray(self.data_blocks)
            for i in range(self.data_blocks):
                message[i] = shards[i][j]
            
            # encode() returns original message + parity
            # We only need the parity part which is the last `parity_blocks` bytes
            encoded_msg = rsc.encode(message)
            parity_bytes = encoded_msg[self.data_blocks:]
            
            for i in range(self.parity_blocks):
                parity_shards[i][j] = parity_bytes[i]
                
        # Combine all shards: first all data shards, then all parity shards
        all_shards = shards + parity_shards
        return b"".join(all_shards)

    def extract_data(self, encoded: bytes, original_data_size: int, erase_pos=None) -> bytes:
        shard_size = len(encoded) // self.total_shards
        
        # Reconstruct shards from the flat encoded bytes
        shards = [bytearray(encoded[i * shard_size : (i + 1) * shard_size]) 
                  for i in range(self.total_shards)]
        
        rsc = RSCodec(self.parity_blocks)
        decoded_shards = [bytearray(shard_size) for _ in range(self.data_blocks)]
        
        # Identify missing shard indices if erase_pos is provided (byte-level)
        # However, our higher-level logic usually works with missing *shards*.
        # RSCodec expects erase_pos to be indices within the MESSAGE (0..total_shards-1).
        
        # Convert byte-level erase_pos to shard indices if necessary.
        # But typically `extract_data` is called with corrupt bytes.
        # For row-based logic, we need to know which *columns* (shards) are corrupted.
        
        # Helper: if erase_pos is passed as linear byte indices, we must map them to shard indices.
        # But standard RSCodec usage in this context implies we know which shards are missing.
        # SIMPLIFICATION: If erase_pos contains ANY byte index falling into shard X, 
        # we treat shard X as erased for that row. 
        
        # Actually, for row-based, `erase_pos` should effectively list the *Indices of missing shards* (0 to total_shards-1).
        # But the legacy API passed linear byte offsets. We need to adapt or rely on `extract_data_blocks` which is cleaner.
        
        # Let's fix `extract_data` to infer shard erasures from global byte positions roughly,
        # OR assume erase_pos lists shard indices if valid. 
        # Given the previous implementation used `erase_pos` relative to linear buffer, 
        # we'll map linear buffer erasures to shard erasures.
        
        erased_shard_indices = set()
        if erase_pos:
            for pos in erase_pos:
                erased_shard_indices.add(pos // shard_size)
        
        erased_shard_indices_list = list(erased_shard_indices)
        
        for j in range(shard_size):
            # Construct the received message (some bytes might be garbage, but we have erase info)
            message = bytearray(self.total_shards)
            for i in range(self.total_shards):
                message[i] = shards[i][j]
            
            try:
                # Decode the stripe
                decoded_msg, _, _ = rsc.decode(message, erase_pos=erased_shard_indices_list)
                
                # Copy back data part
                for i in range(self.data_blocks):
                    decoded_shards[i][j] = decoded_msg[i]
            except ReedSolomonError as e:
                raise ValueError(f"Decoding error at byte {j}: {str(e)}")
                
        # Combine data shards
        full_data = b"".join(decoded_shards)
        return full_data[:original_data_size]

    def extract_data_blocks(self, blocks, original_data_size: int) -> bytes:
        if not blocks:
            raise ValueError("No blocks provided")
        
        # Filter None to find shard size
        valid_block = next((b for b in blocks if b is not None), None)
        if valid_block is None:
            raise ValueError("All blocks are missing")
            
        shard_size = len(valid_block)
        if len(blocks) != self.total_shards:
            raise ValueError(f"Expected {self.total_shards} blocks, got {len(blocks)}")
            
        # Identify missing shard indices
        erase_pos = [i for i, b in enumerate(blocks) if b is None]
        
        # Fill missing blocks with zeros for processing (RSCodec handles erasures via erase_pos)
        shards = [bytearray(b) if b is not None else bytearray(shard_size) for b in blocks]
        
        rsc = RSCodec(self.parity_blocks)
        decoded_data = bytearray()
        
        # Pre-allocate output buffer
        decoded_shards = [bytearray(shard_size) for _ in range(self.data_blocks)]
        
        for j in range(shard_size):
            stripe = bytearray(self.total_shards)
            for i in range(self.total_shards):
                stripe[i] = shards[i][j]
            
            try:
                # decode returns the original DATA part + parity part (corrected)
                # But RSCodec.decode usually returns just the message part (data) if configured?
                # Actually rsc.decode(msg) returns (decoded_msg, ecc_msg, errata_pos)
                # where decoded_msg is the data portion if nsym was used correctly?
                # No, RSCodec(nsym) treats input as (data + ecc).
                # The 'data' length is len(input) - nsym.
                # So if input is `total_shards` long, output data is `data_blocks` long.
                
                decoded_stripe, _, _ = rsc.decode(stripe, erase_pos=erase_pos)
                
                # Copy back to decoded shards
                for i in range(self.data_blocks):
                    decoded_shards[i][j] = decoded_stripe[i]
                    
            except ReedSolomonError as e:
                 raise ValueError("Decoding error: " + str(e))
                 
        full_data = b"".join(decoded_shards)
        return full_data[:original_data_size]
