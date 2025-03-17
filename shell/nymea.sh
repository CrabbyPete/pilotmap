echo -e "deb http://repository.nymea.io $(lsb_release -s -c) main" | sudo tee /etc/apt/sources.list.d/nymea.list
sudo wget -O /etc/apt/trusted.gpg.d/nymea.gpg https://repository.nymea.io/nymea.gpg

sudo apt-get update
sudo apt-get install nymea-networkmanager dirmngr

sudo systemctl enable nymea-networkmanger

sudo systemctl disable dhcpcd