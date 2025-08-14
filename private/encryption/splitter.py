import io
from typing import Optional, BinaryIO, Iterator

from .encryption import encrypt


class Splitter:
    
    def __init__(self, key: bytes, reader: BinaryIO, block_size: int):
        self.key = key
        self.reader = reader
        self.block_size = block_size
        self.counter = 0
        self._eof_reached = False
        
    def next_bytes(self) -> Optional[bytes]:
        if self._eof_reached:
            return None
            
        try:
            data = self.reader.read(self.block_size)
            
            if not data:
                self._eof_reached = True
                return None
                
            info_string = f"block_{self.counter}"
            info = info_string.encode('utf-8')
            
            encrypted_data = encrypt(self.key, data, info)
            
            self.counter += 1
            
            return encrypted_data
            
        except Exception as e:
            raise Exception(f"splitter error: {str(e)}")
    
    def __iter__(self) -> Iterator[bytes]:
        while True:
            chunk = self.next_bytes()
            if chunk is None:
                break
            yield chunk
    
    def reset(self, new_reader: Optional[BinaryIO] = None):
        
        if new_reader is not None:
            self.reader = new_reader
        else:
            if hasattr(self.reader, 'seek'):
                self.reader.seek(0)
            
        self.counter = 0
        self._eof_reached = False


def new_splitter(key: bytes, reader: BinaryIO, block_size: int) -> Splitter:
    if len(key) == 0:
        raise ValueError("encryption key cannot be empty")
    
    if len(key) != 32:
        raise ValueError("encryption key must be 32 bytes long")
        
    return Splitter(key, reader, block_size) 