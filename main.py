#! /usr/bin/env python
#
# Developer: YaAlex (yaalex.xyz)

import struct
import os
import zlib
import io
import subprocess
import sys


help_message = f"""Usage: {sys.argv[0]} <kernel>

Description:
    Makes 32bit SAR kernels boot ramdisk.
    Refer to README.md for additional instructions."""


def main():
    if len(sys.argv) == 1:
        sys.exit(help_message)
    elif sys.argv[1] in ['-h', '--help']:
        sys.exit(help_message)
    zimg_fn = sys.argv[1]
    # Check given file
    if os.path.exists(zimg_fn):
        zimg_fn = os.path.abspath(zimg_fn)
    else:
        raise Exception('File not found')
    patch(zimg_fn)


def printi(text):
    print(f"INFO: {text}")


# ------------------------------------------------------
# Patch

def patch(zimg_fn):
    try:
        new_zimg_fn = f"{zimg_fn}-p"

        p7z_cmd = [
            '7z', 'a', 'dummy', '-tgzip', '-si', '-so', '-mx5', '-mmt4']

        with open(zimg_fn, 'rb') as zimg_file:
            zimg_file.seek(0x24)
            data = struct.unpack("III", zimg_file.read(4 * 3))
            if (data[0] != 0x016f2818):
                raise Exception(
                    "ERROR: Can't found IMG magic number")

            zimg_size = data[2]
            zfile_size = os.path.getsize(zimg_fn)
            if (zfile_size < zimg_size):
                raise Exception(
                    f"ERROR: zImage size: {zfile_size} (expected: {zimg_size})")

            zimg_footer = ''
            if (zfile_size > zimg_size):
                zimg_file.seek(zimg_size)
                zimg_footer = zimg_file.read()

            zimg_file.seek(0)
            zimg = zimg_file.read(zimg_size)
            gz_begin = zimg.find(b'\x1F\x8B\x08\x00')
            if (gz_begin < 0x24):
                raise Exception(
                    "ERROR: Can't found GZIP magic header. Your image is either already patched or corrupted.")

        zimg_file = io.BytesIO()
        zimg_file.write(zimg)

        zimg_file.seek(gz_begin + 8)
        data = struct.unpack("BB", zimg_file.read(2))
        ext_flags = data[0]
        if ext_flags not in [2, 4]:
            raise Exception(
                f"ERROR: Can't support extra flags = 0x{ext_flags}")

        zimg_file.seek(gz_begin)
        gz_data = zimg_file.read()

        printi('Unpacking kernel data...')
        kernel_data = zlib.decompress(gz_data, 16 + zlib.MAX_WBITS)
        if (kernel_data is None):
            raise Exception(
                "ERROR: Can't decompress GZIP data")
        if b'skip_initramfs' not in kernel_data:
            raise Exception(
                "ERROR: Didn't find skip_initramfs, no need to patch.")
        # Patch kernel data
        printi('Patching kernel data...')
        kernel_data = kernel_data.replace(b'skip_initramfs',
                                          b'want_initramfs')
        printi('Packing kernel data...')
        p7zc = subprocess.run(p7z_cmd, input=kernel_data, capture_output=True)
        if p7zc.returncode != 0:
            raise Exception(f'ERROR: p7z ended with an error. stderr: {p7zc.stderr}')
        new_gz_data = p7zc.stdout

        # Find proper end of gzip block by finding the size
        kernel_size = len(kernel_data)
        kernel_sz = struct.pack("I", kernel_size)
        gz_end = zimg.rfind(kernel_sz)
        if (gz_end < len(zimg) - 0x1000):
            raise Exception(
                "ERROR: Can't find ends of GZIP data (gz_end = 0x{gz_end}). Your image is either already patched or corrupted.")

        # Check if size isn't bigger so we don't overlap
        # (won't happen since its smaller 100% of the time)
        gz_end = gz_end + 4
        gz_size = gz_end - gz_begin
        new_gz_size = len(new_gz_data)
        if (new_gz_size > gz_size):
            raise Exception(
                "ERROR: Can't new GZIP size too large")
        printi('Getting all back together...')
        with open(new_zimg_fn, 'w+b') as new_zimg_file:
            zimg_file.seek(0)
            new_zimg_file.write(zimg_file.read(gz_begin))
            new_zimg_file.write(new_gz_data)
            # Pad with zeroes
            new_zimg_file.write(b'\0' * (gz_size - new_gz_size))
            # Write dtbs at the end
            zimg_file.seek(gz_end)
            new_zimg_file.write(zimg_file.read())
            new_zimg_file.write(zimg_footer)
            zimg_file.close()
            new_zimg_file.seek(0)
            # Search for gzip size pos
            pos = zimg.find(struct.pack("I", gz_end - 4))
            if (pos < 0x24 or pos > 0x400 or pos > gz_begin):
                raise Exception(
                    "ERROR: Can't find offset of orig GZIP size field")
            new_zimg_file.seek(pos)
            # Write new gz size
            new_zimg_file.write(struct.pack("I", gz_begin + new_gz_size - 4))
        return True

    except Exception as errp:
        print(str(errp))
        return False


if __name__ == "__main__":
    main()
