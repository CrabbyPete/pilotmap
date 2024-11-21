This is the code for PilotMap. In order to install the code on a Raspberry Pi do the following
steps.

1. Create a headless Raspberry Pi image with the latest version. 

2. With a fresh Pi, SSH into the Pi with the network name, SSID, SSID password, user name that and user password used with the Raspberry  Pi Imager
3. Once logged in run the following commands
   1. sudo apt -y update
   2. sudo apt -y install git python3-venv
   3. git clone https://github.com/CrabbyPete/pilotmap.git
   4. python -m venv --system-site-packages venv
   5. chmod + ./pilotmap/shell/install.sh
   6. source ./pilotmap/shell/install.sh 
