import os
import json
import subprocess
import ipaddress

# Check if running as root
if os.getuid() == 0:
    print('Script Starting')
else:
    print('This needs to be run as root access. Exiting now.')
    print('Restart the script using sudo')
    quit()

# ThousandEyes Raspberry Pi image customizer
# Script created by Dan Kelcher
# Github page: https://github.com/mytechgnome/TE-Imaging
# Script documentation: https://www.mytechgnome.com/2023/06/13/automated-thousandeyes-raspberry-pi-image-customization/
# Follow me on LinkedIn: https://www.linkedin.com/in/dkelcher/ and Twitter: https://twitter.com/Ipswitch

def list_usb_storage_devices():
    # Run 'lsblk' command to get the list of block devices
    output = subprocess.check_output(['lsblk', '-o', 'NAME,TRAN', '-n', '-l', '-b'], universal_newlines=True)

    # Parse the output to extract USB storage devices
    devices = []
    lines = output.splitlines()
    for line in lines:
        parts = line.strip().split()
        if len(parts) >= 2 and parts[1] == 'usb':
            devices.append(parts[0])

    return devices

print('!!! WARNING !!!')
print('This process will attempt to erase and flash SD cards')
print('This may result in data loss')
print('Verify the location before confirming!')
print('!!! WARNING !!!')

# Load data from vars.json into variables
with open('vars.json') as f:
  data = json.load(f)

# Set variables
token = (data['token'])
image = (data['image_name'])
ssh = (data['sshKey'])
img = image[:-3]
user = subprocess.check_output("echo $SUDO_USER", shell=True)
user = user.strip()
user = user.decode('utf-8')
path = os.path.join('/home',user)

print('Checking for image: '+image)
# Check for downloaded image
imagePath = os.path.join(path,image)
if os.path.isfile(imagePath):
   print("Image found")
else:
    print("Downloading image")
    # Download image
    os.system('wget https://app.thousandeyes.com/install/downloads/appliance/'+image)

print('Checking if images has been decompressed.')
if os.path.isfile(img):
   print("Image decompressed")
else:
    print("Decompressing image - this may take some time")
    # Uncompress the image
    os.system('unxz -k '+image)

# Create a mountpoint
print('Checking for mountppoint')
if os.path.exists('/tmp/temount/'):
    print('Mountpoint exists.')
else:
    print('Creating mountpoint at /tmp/temount')
    os.system('mkdir /tmp/temount')

# Mount the image
print('Mounting the image')
os.system('mount -o loop,offset=269484032 '+img+' /tmp/temount/')
print('Image mounted')

# Apply Global configs
print('Applying global configs')

# Add account token
os.system("sed -i 's/<account-token>/"+token+"/g' /tmp/temount/etc/te-agent.cfg")

# Add SSH key
if ssh == "":
    print("No SSH key provided")
else:
    os.system('echo '+ssh+' >> /tmp/temount/etc/ssh/keys/thousandeyes/authorized_keys')

# Add documentation link to image
os.system('echo ThousandEyes Raspberry Pi image customizer >> /root/build.txt')
os.system('echo Script created by Dan Kelcher >> /root/build.txt')
os.system('echo Github page: https://github.com/mytechgnome/TE-Imaging >> /root/build.txt')
os.system('echo Script documentation: https://www.mytechgnome.com/2023/06/13/automated-thousandeyes-raspberry-pi-image-customization/ >> /root/build.txt')
os.system('echo Follow me on LinkedIn: https://www.linkedin.com/in/dkelcher/ and Twitter: https://twitter.com/Ipswitch >> /root/build.txt')

# Collect hostname, IP, and DNS config files
if os.path.exists('/tmp/teconfigs/'):
    print('Config folder exists.')
else:
    os.system('mkdir /tmp/teconfigs')
os.system('cp -p /tmp/temount/etc/network/interfaces /tmp/teconfigs/interfaces')
os.system('cp -p /tmp/temount/etc/hostname /tmp/teconfigs/hostname')
os.system('cp -p /tmp/temount/etc/systemd/resolved.conf /tmp/teconfigs/resolved.conf')

# Set device-specific variables
devices = data["Devices"]
for device in devices:
    hostname = device["Hostname"]
    ip = device["IP"]
    mask = device["Subnet_Mask"]
    # Find broadcast address from IP and subnet
    network = ipaddress.IPv4Network(ip + '/' + mask, strict=False)
    broadcast = str(network.broadcast_address)
    gateway = device["Gateway"]
    dns1 = device["DNS1"]
    dns2 = device["DNS2"]
    if dns2 == "":
        dns = dns1
    else:
        dns = dns1+' '+dns2

    # Check if image is mounted
    print('Checking for mountppoint')
    if os.path.exists('/tmp/temount/etc/'):
        print('Image mounted.')
    else:
        print('Mounting image')
        os.system('mount -o loop,offset=269484032 '+img+' /tmp/temount/')

    # Restore default configuration files
    os.system('cp -p /tmp/teconfigs/interfaces /tmp/temount/etc/network/interfaces')
    os.system('cp -p /tmp/teconfigs/hostname /tmp/temount/etc/hostname')
    os.system('cp -p /tmp/teconfigs/resolved.conf /tmp/temount/etc/systemd/resolved.conf')

    # Change hostname
    os.system("sed -i 's/tepi/"+hostname+"/g' /tmp/temount/etc/hostname")

    # Set IP
    if ip == "DHCP":
        print("Using DHCP addressing")
    else:
        print("Assigning IP address")
        os.system("sed -i 's/dhcp/static/g' /tmp/temount/etc/network/interfaces")
        os.system('echo address '+ip+' >> /tmp/temount/etc/network/interfaces')
        os.system('echo netmask '+mask+' >> /tmp/temount/etc/network/interfaces')
        os.system('echo broadcast '+broadcast+' >> /tmp/temount/etc/network/interfaces')
        os.system('echo gateway '+gateway+' >> /tmp/temount/etc/network/interfaces')
    # Add DNS servers
        os.system("sed -i 's/#DNS=/DNS= "+dns+"/g' /tmp/temount/etc/systemd/resolved.conf")

    # Unmount image
    os.system('umount /tmp/temount')
    print("Image customization complete for "+hostname)

    # List USB storage devices
    target = 0
    while target == 0:
        usb_devices = list_usb_storage_devices()
        if len(usb_devices) == 1:
            for device in usb_devices:
                target = device
                print("Image will be flashed to "+target)
        elif usb_devices:
            print("USB Storage Devices:")
            for device in usb_devices:
                print(device)
            destination = input("Please enter the USB target")
            while destination not in usb_devices:
                print("The target did not match an existing device.")
                destination = input("Please enter the USB target")
            target = destination
            print("Image will be flashed to "+target)
        else:
            print("No USB storage devices found.")
            print('Insert SD card into USB adapter, and plug in the adapater.')
            print('Press Enter to scan for USB devices again.')
            input()

    # Flash SD card
    input("Press Enter to begin flashing")
    os.system('dd if='+img+' of=/dev/'+target+' status=progress')

    print("Please remove the SD card. If more cards need to be flashed insert the next card now.")
    input("Press Enter to continue.")

# Flashing complete
print('All images completed')

# Clean up
print('Cleaning up image files.')
if os.path.exists('/tmp/teconfig/'):
    os.system('rm /tmp/teconfigs/*')
    os.system('rmdir /tmp/teconfigs/')
if os.path.exists('/tmp/temount/etc/'):
    os.system('umount /tmp/temount')
if os.path.exists('/tmp/temount/'):
    os.system('rmdir /tmp/temount')
if os.path.isfile(img):
    os.system('rm thousandeyes-appliance.rpi4.img')
input('Cleanup complete. Press Enter to exit the script.')
quit()