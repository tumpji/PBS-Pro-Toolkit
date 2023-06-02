

USERNAME=$USER

kinit -r 7d "${USERNAME}@META"

echo "The Kerberos is now ready to use"
