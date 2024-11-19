sudo apt update -y
sudo apt upgrade -y
sudo apt install -y git emacs-nox redis
sudo apt install -y python3-pip python3-venv  python3-numpy
sudo apt install -y libopenjp2-7
sudo apt install -y nginx
sudo apt install ttf-mscorefonts-installer
sudo apt install i2c-tools
sudo raspi-config nonint do_i2c 0


python3 -m venv --system-site-packages pilotmap
cd pilotmap
source bin/activate
git clone https://github.com/CrabbyPete/pilotmap.git
pip3 install -r requirements.txt
chmod +x setup.sh
setup.sh

