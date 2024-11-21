# git clone https://github.com/CrabbyPete/pilotmap.git
#python3 -m venv --system-site-packages ~/venv
source ~/venv/bin/activate

# sudo apt update -y
# sudo apt upgrade -y
sudo apt install -y git emacs-nox redis
sudo apt install -y python3-pip python3-venv  python3-numpy
sudo apt install -y libopenjp2-7
sudo apt install -y nginx
sudo apt install ttf-mscorefonts-installer
sudo apt install i2c-tools
sudo raspi-config nonint do_i2c 0

cd pilotmap
pip3 install -r ./src/requirements.txt
chmod +x ./shell/setup.sh
./shell/setup.sh

