sudo apt update -y
sudo apt upgrade -y
sudo apt install -y git emacs-nox redis
sudo apt install -y python3-pip python3-venv  python3-numpy libopenjp2-7
sudo apt install -y nginx uwsgi uwsgi-plugin-python3
sudo raspi-config nonint do_i2c 0

python3 -m venv --system-site-packages pilotmap
cd pilotmap
source bin/activate

