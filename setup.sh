#!/bin/bash

# update apt-get and required packages
sudo apt-get update
sudo apt-get install python-pip libpq-dev python-dev libxml2-dev libxslt1-dev libldap2-dev libsasl2-dev libffi-dev
sudo pip install -r requirements.txt
