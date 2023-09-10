#!/bin/bash

cp home_aquaponics.service /etc/systemd/system/home_aquaponics.service

touch /var/log/home-aquaponics.log
chmod 666 /var/log/home-aquaponics.log

