#!/bin/bash

### Install git and docker
yum install git
yum install docker

### Install docker compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.3/docker-compose-$(uname -s)-$(uname -m)"  -o /usr/local/bin/docker-compose
sudo mv /usr/local/bin/docker-compose /usr/bin/docker-compose
sudo chmod +x /usr/bin/docker-compose

### First time cloning the frontend repo from submodule
git submodule init
git submodule update

### Pull latest from each submodule
git submodule foreach 'git pull origin main'

### Start docker
sudo systemctl start docker

### Start the symphony
sudo docker-compose down
sudo docker-compose up --build -d