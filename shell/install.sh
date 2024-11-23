# git clone https://github.com/CrabbyPete/pilotmap.git
#python3 -m venv --system-site-packages ~/venv
set -x
source ~/venv/bin/activate

# sudo apt update -y
# sudo apt upgrade -y
sudo apt install -y git emacs-nox redis
sudo apt install -y python3-pip python3-venv  python3-numpy
sudo apt install -y libopenjp2-7
sudo apt install -y nginx
sudo apt install -y ttf-mscorefonts-installer
sudo apt install -y i2c-tools
sudo raspi-config nonint do_i2c 0

wget https://www.1001fonts.com/download/arrows.zip
sudo unzip arrows.zip -d /usr/share/fonts/truetype/misc

pip3 install -r ./pilotmap/src/requirements.txt
chmod +x ./pilotmap/shell/setup.sh
sudo source ./pilotmap/shell/setup.sh

