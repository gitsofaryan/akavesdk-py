# Akave SDK for Python

The Akave SDK for Python provides a simple interface to interact with the Akave platform. It enables you to store and manage files securely on the Akave decentralized storage network.

## Installation

You can install the SDK using pip:

```bash
pip install akavesdk
```

Or install directly from GitHub:

```bash
pip install git+https://github.com/d4v1d03/akavesdk-py.git
```

## Authentication

The Akave SDK uses two main authentication methods:

1. **Wallet-based authentication** - This uses Ethereum wallet private keys for IPC operations on the blockchain. This is required for operations that require blockchain transactions (creating buckets, managing file permissions, etc.).

2. **Standard API connection** - Basic operations like file uploads/downloads use gRPC connections to Akave nodes.

You can set up your authentication in several ways:

### Environment variables (recommended)

```bash
# Set these environment variables
export AKAVE_NODE="api.akave.io:50051"  # Default Akave API endpoint
export AKAVE_PRIVATE_KEY="your_ethereum_private_key"  # Optional, for blockchain operations
export AKAVE_ENCRYPTION_KEY="your_32_byte_encryption_key"  # Optional, for file encryption
```

### Direct initialization

```python
from akavesdk import SDK

# Initialize with explicit parameters
sdk = SDK(
    address="api.akave.io:50051",
    max_concurrency=4,
    block_part_size=1 * 1024 * 1024,  # 1MB
    use_connection_pool=True,
    private_key="your_ethereum_private_key",  # Optional
    encryption_key=b"your_32_byte_encryption_key"  # Optional
)
```

### Getting credentials

To obtain Akave credentials:

1. Create an account on the [Akave platform](https://akave.io)
2. Generate API keys from your account dashboard
3. For wallet-based authentication, use an Ethereum wallet private key

## Usage

### Basic Usage

```python
from akavesdk import SDK

# Initialize the SDK
sdk = SDK(
    address="api.akave.io:50051",
    max_concurrency=4,
    block_part_size=1 * 1024 * 1024,  # 1MB
    use_connection_pool=True
)

try:
    # Create a bucket
    bucket_result = sdk.create_bucket({}, "my-bucket")
    print(f"Created bucket: {bucket_result.name}")
    
    # List all buckets
    buckets = sdk.list_buckets({})
    for bucket in buckets:
        print(f"Bucket: {bucket.name}, Created: {bucket.created_at}")
finally:
    # Always close the connection when done
    sdk.close()
```

### Streaming API Usage

```python
from akavesdk import SDK

# Initialize the SDK
sdk = SDK(
    address="api.akave.io:50051",
    max_concurrency=4,
    block_part_size=1 * 1024 * 1024,
    use_connection_pool=True
)

try:
    # Get streaming API
    streaming = sdk.streaming_api()
    
    # List files in a bucket
    files = streaming.list_files({}, "my-bucket")
    for file in files:
        print(f"File: {file.name}, Size: {file.size} bytes")
    
    # Get file info
    file_info = streaming.file_info({}, "my-bucket", "my-file.txt")
    print(f"File info: {file_info}")
finally:
    sdk.close()
```

## Development

To set up the development environment:

1. Clone the repository:
```bash
git clone https://github.com/d4v1d03/akavesdk-py.git
cd akavesdk-py
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -e .
```

4. Run tests:
```bash
pytest
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
