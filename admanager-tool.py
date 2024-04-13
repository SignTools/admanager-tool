#!/usr/bin/env python3

import argparse
from pathlib import Path

xor_key = "1A F2 53 18 69 76 B7 A8 00 C2 1A F2 53 18 69 76 B7 A8 00 C2"
xor_key = bytes.fromhex(xor_key)


def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def unpack(src_file: Path, dst_dir: Path):
    assert src_file.is_file(), "Source must be a file"

    with open(src_file, "rb") as f:

        def read_xor(size: int):
            result = bytearray(f.read(size))
            for i, _ in enumerate(result):
                result[i] ^= xor_key[i % len(xor_key)]
            return result

        def get_int(x: bytes):
            return int.from_bytes(x, "little")

        count = get_int(read_xor(4))
        header_size = 4 * count + 4

        f.seek(0, 0)
        header = read_xor(header_size)
        name_list = read_xor(header_size - 4)
        # TODO: Not currently used
        thumb_list = read_xor(header_size - 4)

        name_list = [get_int(x) for x in chunks(name_list, 4)]
        names = []
        for offset in name_list:
            f.seek(offset, 0)
            size = get_int(read_xor(4))
            names.append(read_xor(size).decode())

        dst_dir.mkdir(exist_ok=True)

        for i, name in enumerate(names):
            offset = get_int(header[4 * i + 4 : 4 * i + 8])
            f.seek(offset, 0)
            size = get_int(read_xor(4))
            with open(dst_dir / name, "wb") as f2:
                offset = 0
                while offset < size:
                    buffer_size = min(0x2000, size - offset)
                    f2.write(read_xor(buffer_size))
                    offset += buffer_size


def pack(src_dir: Path, dst_file: Path):
    assert src_dir.is_dir(), "Source must be a directory"

    with open(dst_file, "wb") as f:

        def write_xor(data: bytes):
            result = bytearray(data)
            for i, _ in enumerate(result):
                result[i] ^= xor_key[i % len(xor_key)]
            f.write(result)

        def get_bytes(x: int):
            return x.to_bytes(4, "little")

        files = sorted(f for f in src_dir.glob("*") if f.is_file())
        file_sizes = [f.stat().st_size for f in files]
        # TODO: Not currently used
        thumbs = [bytes(1) for i in range(len(files))]

        count = len(files)
        header_size = 4 * count + 4
        name_list_size = 4 * count
        thumb_list_size = 4 * count

        header = get_bytes(len(files))
        name_list = bytes(0)
        thumb_list = bytes(0)
        offset = header_size + name_list_size + thumb_list_size
        for i, file in enumerate(files):
            header += get_bytes(offset)
            name_offset = offset + 4 + file_sizes[i]
            name_list += get_bytes(name_offset)
            thumb_offset = name_offset + 4 + len(file.name)
            thumb_list += get_bytes(thumb_offset)
            offset = thumb_offset + 4 + len(thumbs[i])

        write_xor(header)
        write_xor(name_list)
        write_xor(thumb_list)

        for i, file in enumerate(files):
            size = file_sizes[i]
            write_xor(get_bytes(size))
            with open(file, "rb") as f2:
                offset = 0
                while offset < size:
                    buffer_size = min(0x2000, size - offset)
                    write_xor(f2.read(buffer_size))
                    offset += buffer_size
            write_xor(get_bytes(len(file.name)))
            write_xor(file.name.encode())
            write_xor(get_bytes(len(thumbs[i])))
            write_xor(thumbs[i])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="TIGI Software Apps Manager backup tool.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="cmd", help="Operation to perform.", required=True)

    pack_parser = subparsers.add_parser("pack", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    unpack_parser = subparsers.add_parser("unpack", formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument(
        "input",
        type=str,
        help="File to read.",
    )
    parser.add_argument(
        "output",
        type=str,
        help="File to save.",
    )

    args = parser.parse_args()
    args.input = Path(args.input)
    args.output = Path(args.output)

    assert args.input.exists(), "Input file does not exist"
    assert args.output.parent.exists(), "Output file's directory does not exist"

    if args.cmd == "unpack":
        print(f"Unpacking {args.input}...")
        unpack(args.input, args.output)
        print("Done! Unpacked to:", args.output)
    else:
        print(f"Packing {args.input}...")
        pack(args.input, args.output)
        print("Done! Packed to:", args.output)
