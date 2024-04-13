# ADManager Tool

This is a simple backup management tool for TIGI Software Apps Manager. It allows you to unpack and repack the encrypted `__private_info`, which contains the backup's keychain dump. The produced file is bit-perfect match of the original.

## Usage

```
TIGI Software Apps Manager backup tool.

positional arguments:
  {pack,unpack}  Operation to perform.
  input          File to read.
  output         File to save.

options:
  -h, --help     show this help message and exit
```

Examples:

```bash
./admanager-tool.py unpack __private_info unpacked
./admanager-tool.py pack unpacked __private_info
```
