#!/bin/bash
cd "$(dirname "$0")";
sleep 5m
./RPi-ServCheck.py T > ./Log/reboot-log 2>&1
