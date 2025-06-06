# UNCtools

A comprehensive toolkit for handling UNC paths, network drives, and substituted drives across different environments.

## Features

- Convert between UNC paths (\\\\server\\share) and local drive paths (Z:\\)
- Detect UNC paths, network drives, and substituted drives
- Handle Windows security zones for improved UNC path access
- Provide high-level file operations that work seamlessly with UNC paths
- Cross-platform compatibility with graceful degradation

## Installation

### Standard Installation

```bash
pip install unctools
```

### With Windows-specific Support

```bash
pip install unctools[windows]
```

### Development Mode

For development and testing:

```bash
git clone https://github.com/yourusername/unctools.git
cd unctools
pip install -e .[dev]
```

## Usage

### Basic Path Conversion

```python
from unctools import convert_to_local, convert_to_unc

# Convert UNC path to local drive path
local_path = convert_to_local("\\\\server\\share\\folder\\file.txt")
# Result (if mapped): "Z:\\folder\\file.txt"

# Convert local drive path back to UNC
unc_path = convert_to_unc("Z:\\folder\\file.txt")
# Result: "\\\\server\\share\\folder\\file.txt"
```

### Path Detection

```python
from unctools import is_unc_path, is_network_drive, is_subst_drive, get_path_type

# Check if a path is a UNC path
if is_unc_path("\\\\server\\share\\file.txt"):
    print("This is a UNC path")

# Check if a drive is a network drive
if is_network_drive("Z:"):
    print("Z: is a network drive")

# Get the type of a path
path_type = get_path_type("C:\\Users\\")
# Result: "local", "network", "subst", "unc", etc.
```

### Safe File Operations

```python
from unctools import safe_open, safe_copy, batch_convert

# Open a file, handling UNC paths automatically
with safe_open("\\\\server\\share\\file.txt", "r") as f:
    content = f.read()

# Copy a file, handling path conversions
safe_copy("\\\\server\\share\\file.txt", "local_copy.txt")

# Convert multiple paths at once
paths = ["\\\\server\\share\\file1.txt", "\\\\server\\share\\file2.txt"]
converted = batch_convert(paths, to_unc=False)
```

### Windows Security Zones

```python
from unctools.windows import fix_security_zone, add_to_intranet_zone

# Fix security zone issues for a server
fix_security_zone("server")

# Add a server to the Local Intranet zone
add_to_intranet_zone("server")
```

### Network Drive Management

```python
from unctools.windows import create_network_mapping, remove_network_mapping

# Create a network drive mapping
success, drive = create_network_mapping("\\\\server\\share", "Z:")

# Remove a network drive mapping
remove_network_mapping("Z:")
```

## Platform Compatibility

UNCtools is designed to work across various platforms:

- **Windows**: Full functionality including security zones and network drive management
- **Linux/macOS**: Basic path conversion and detection, with graceful degradation for Windows-specific features

## Development

### Running Tests

```bash
pytest
```

### Code Style

```bash
black unctools
flake8 unctools
```

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
