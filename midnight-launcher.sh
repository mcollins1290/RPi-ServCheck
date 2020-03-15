#!/bin/bash
cd "$(dirname "$0")";
./RPi-ServCheck.py T > ./Log/midnight-log 2>&1
