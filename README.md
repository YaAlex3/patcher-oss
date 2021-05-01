# Boot Image Patcher [arm32 sar boot image patcher] v1 OSS
  Patcher to make kernel boot ramdisk on ARM32 SaR devices.

### Requirements:
#### Windows:
- 7-Zip (download and install)
#### Linux:
- p7zip-full (install using your distro's package manager)
#### Common:
- python (latest)
- arm32-SAR boot image
- any boot image repacking tool out there
### Short Instructions:
- Unpack your boot image yourself using preferred tools
- Supply kernel (zImage) as first argument to the main.py script in the source tree
- Output file will be named like this: "inputfile-p"
- Repack boot image with patched kernel
- Flash the new boot image
