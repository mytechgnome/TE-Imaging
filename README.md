# TE-Imaging
Script for creating customized ThousandEyes agent images for Raspberry Pi deployments.

How to use the script:
1. Update the vars.json file with your account token
2. If you want to include an SSH key, add it to vars.json
3. Add the device-specific info (hostname, IP, etc.)

Run the script using sudo because it will need to mount/unmount images and write to the SD card.

!!WARNING!! The process will attempt to overwrite USB media. This can cause data loss. Make sure the device name is correct before writing to the SD card
