
USERNAME=$USER

sudo apt-get install krb5-user


sudo scp "${USERNAME}@skirit.metacentrum.cz:/etc/krb5.conf" /etc/
#sudo metaconnect --scp /etc/krb5.conf /etc/

echo "
# Kerberos access (Metacentrum)
GSSAPIAuthentication yes
GSSAPIDelegateCredentials yes
GSSAPIKeyExchange yes
" >> ~/.ssh/config


