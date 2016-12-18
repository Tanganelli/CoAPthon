#!/usr/bin/env bash

apt-get update
apt-get install -y git
apt-get install -y python-pip
if ! [ -d CoAPthon ]; then
	git clone https://github.com/Tanganelli/CoAPthon.git
else
	cd CoAPthon
	git pull
fi
