# UNCtools Package Structure

```
unctools/
│
├── unctools/               # Main package directory
│   ├── __init__.py        # Package initialization, exposes public API
│   ├── converter.py       # Path conversion functions (UNC ↔ local)
│   ├── detector.py        # Path type detection (UNC, network drive, subst)
│   ├── windows/           # Windows-specific functionality
│   │   ├── __init__.py    
│   │   ├── registry.py    # Registry and security zone operations
│   │   ├── network.py     # Network share operations
│   │   └── security.py    # Windows security handling
│   ├── utils/             # Utility functions
│   │   ├── __init__.py
│   │   ├── logger.py      # Configurable logging
│   │   ├── compat.py      # Cross-platform compatibility
│   │   └── validation.py  # Path validation utilities
│   └── operations.py      # High-level file operations (batch conversion, etc.)
│
├── tests/                 # Test suite
│   ├── __init__.py
│   ├── test_converter.py
│   ├── test_detector.py
│   ├── test_windows.py
│   └── test_operations.py
│
├── examples/              # Example usage scripts
│   ├── basic_usage.py
│   ├── windows_zone_fix.py
│   └── batch_operations.py
│
├── pyproject.toml         # Project metadata (PEP 621)
├── setup.py               # Installation script
├── setup.cfg              # Package configuration
├── README.md              # Project documentation
├── LICENSE                # License file
└── .gitignore             # Git ignore file
```

## Dependency Strategy

The package will have:

1. **Core dependencies**: minimal, required for basic functionality 
2. **Optional dependencies**: for extended functionality
3. **Fallback implementations**: when dependencies aren't available

For example:
- Core functionality will work without `pywin32`, but will provide enhanced capabilities when available
- Windows-specific features will gracefully degrade on other platforms
- Advanced features can be imported separately to avoid unnecessary dependencies

## Key Modules & Functionality

### Core Layer

- **`__init__.py`**: Exposes public API, simplifies imports
- **`converter.py`**: Core path conversion functionality
- **`detector.py`**: Path type detection and analysis

### Windows-Specific Layer

- **`windows/registry.py`**: Registry operations, security zone management
- **`windows/network.py`**: Network share operations (`net use`, etc.)
- **`windows/security.py`**: Windows security and permissions

### Utility & Operation Layer

- **`utils/logger.py`**: Detailed logging with configurable verbosity
- **`utils/compat.py`**: Cross-platform compatibility helpers
- **`operations.py`**: High-level operations (batch conversion, file operations)

## Planned Public API

```python
# Basic path conversion
from unctools import convert_to_local, convert_to_unc, normalize_path

# Path detection
from unctools import is_unc_path, is_network_drive, is_subst_drive

# Windows-specific features (optional)
from unctools.windows import fix_security_zone, get_network_mappings

# High-level operations
from unctools import safe_open, batch_convert, batch_copy
```

## Installation and Development Setup

**Regular installation:**
```
pip install unctools
```

**Development mode:**
```
git clone https://github.com/yourusername/unctools.git
cd unctools
pip install -e .
```

**With optional dependencies:**
```
pip install unctools[windows]  # Install with Windows-specific dependencies
```
