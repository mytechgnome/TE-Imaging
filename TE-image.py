import os
import json
import subprocess
import re

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

#Set device-specific variables
devices = data["Devices"]
for device in devices:
    hostname = device["Hostname"]
    ip = device["IP"]
    mask = device["Subnet_Mask"]
    broadcast = device["Broadcast"]
    gateway = device["Gateway"]
    dns = device["DNS"]

    print("Customizing image for "+hostname)
    uniqueImg = hostname+'.img'
    # Create unique image file
    print('Creating unique image file - '+uniqueImg)
    os.system('rsync --progress '+img+' '+uniqueImg)

    # Mount the image
    print('Mounting image - this may take some time')
    os.system('mount -o loop,offset=269484032 '+uniqueImg+' /tmp/temount/')
    print('Image mounted')

    # Add account token
    os.system("sed -i 's/<account-token>/"+token+"/g' /tmp/temount/etc/te-agent.cfg")

    # Change hostname
    os.system("sed -i 's/tepi/"+hostname+"/g' /tmp/temount/etc/hostname")
    
    # Add SSH key
    if ssh == "":
        print("No SSH key provided")
    else:
        os.system('mkdir /tmp/temount/home/thousandeyes/.ssh')
        os.system('echo '+ssh+' >> /tmp/temount/home/thousandeyes/.ssh/authorized_keys')
    os.system('chmod 700 /tmp/temount/home/thousandeyes/.ssh')
    os.system('chmod 600 /tmp/temount/home/thousandeyes/.ssh/authorized_keys')
	
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
        os.system('echo dns-nameservers '+dns+' >> /tmp/temount/etc/network/interfaces')
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
    input("Press Enter to begin flashing")
    os.system('dd if='+uniqueImg+' of=/dev/'+target+' status=progress')
    print("Flash complete. Please remove the SD card. If more cards need to be flashed insert the next card now.")
    os.system('rm '+uniqueImg)
    input("Press Enter to continue.")
        
