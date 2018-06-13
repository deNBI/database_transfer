#!/bin/bash

sudo apt-get install software-properties-common
sudo apt-add-repository ppa:ansible/ansible
sudo apt-get update
sudo apt-get install ansible

sudo ansible-pull -o -U https://github.com/deNBI/database_transfer.git -C cvmfs_client_ansible > /dev/null
