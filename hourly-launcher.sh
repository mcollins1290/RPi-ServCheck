#!/bin/bash
cd "$(dirname "$0")";
./RPi-ServCheck.py F > ./Log/hourly-log 2>&1
