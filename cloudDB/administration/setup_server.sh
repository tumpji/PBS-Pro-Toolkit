#!/bash/sh
# only for Ubuntu 22.04 LTS



# ---------------------------------------------------------------------------------
# update of the system

sudo apt-get update
sudo apt-get upgrade -y 

sudo apt-get install -y gnupg vim git zsh


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

sudo systemctl enable mongod
sudo reboot





# Manual: /etc/mongo
# net:
#  port: 27017
#  bindIp: 0.0.0.0
# security:
#  authorizaton: enabled



#sudo systemctl start mongod

