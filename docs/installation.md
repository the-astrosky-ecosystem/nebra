# Installation

## Prerequisites
- Python 3.11 or later
- `uv` (for dependency management)

## Install Nebra

### From PyPI
```bash
pip install nebra
```

### From Source
```bash
git clone https://github.com/emilyhunt/nebra.git
cd nebra
uv sync
```

## Optional Dependencies
Nebra supports optional dependencies for additional functionality:

### Kafka Subscriptions
To use Kafka subscriptions (e.g., for GCN notices), install with:
```bash
pip install "nebra[subscriptions]"
```