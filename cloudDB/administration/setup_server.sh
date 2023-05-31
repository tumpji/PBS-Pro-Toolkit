#!/bash/sh
# only for Ubuntu 22.04 LTS


# ---------------------------------------------------------------------------------
# update of the system

sudo apt-get update
sudo apt-get upgrade -y 

sudo apt-get install -y gnupg vim git zsh


# ---------------------------------------------------------------------------------
# set up this repository

git clone https://github.com/tumpji/PBS-Pro-Toolkit.git


# ---------------------------------------------------------------------------------
# setup python

sudo apt-get install -y python3-kerberos python3.11 python3.11-dev python3-pip libsnappy-dev

sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1
pip3 install -r ~/PBS-Pro-Toolkit/cloudDB/requirements.txt


# ---------------------------------------------------------------------------------
# installation of MongoDB

curl -fsSL https://pgp.mongodb.com/server-6.0.asc | \
   sudo gpg -o /usr/share/keyrings/mongodb-server-6.0.gpg \
   --dearmor

echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-6.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/6.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list

sudo apt-get update
sudo apt-get install -y mongodb-org

echo "mongodb soft nofile 65535" | sudo tee -a /etc/security/limits.conf
echo "mongodb hard nofile 65535" | sudo tee -a /etc/security/limits.conf

sudo sysctl -w vm.max_map_count=262144
echo "vm.max_map_count=262144" | sudo tee -a /etc/sysctl.conf

sudo systemctl enable mongod
sudo systemctl start mongod

mongosh --file ~/PBS-Pro-Toolkit/cloudDB/administration/setup_users.js

sudo sed 's/bindIp:.*/bindIp: 0.0.0.0/' -i /etc/mongod.conf
echo "security:\n authorization: enabled" | sudo tee -a /etc/mongod.conf


# ---------------------------------------------------------------------------------
# reboot

sudo reboot









