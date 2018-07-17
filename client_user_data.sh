#!/bin/bash

# try to wait until we are online
while ! ping -c 1 heise.de; do
	sleep 2
done
sudo apt-get install software-properties-common --yes
sudo apt-add-repository ppa:ansible/ansible --yes
sleep 30
sudo apt-get update --yes
while [[ ! -f /var/lib/dpkg/lock ]]; do
	sleep 2
done
sudo apt-get install ansible --yes

wget https://raw.githubusercontent.com/thestinger/termite/master/termite.terminfo
tic -x termite.terminfo

sudo ansible-pull -o -U https://github.com/deNBI/database_transfer.git -C cvmfs_client_ansible > /dev/null
