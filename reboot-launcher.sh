#!/bin/bash
LOGTOSQL=true

cd "$(dirname "$0")";
sleep 5m
touch reboot
./RPi-ServCheck.py T > ./Log/reboot-log 2>&1
retVal=$?

if [ "$LOGTOSQL" = true ] ; then
	logtext=$(cat ./Log/reboot-log)
	echo 'Logging to Pi Health Check MariaDB enabled'
	result=$(curl -G --data-urlencode "code=SERV" \
			 --data-urlencode "status=${retVal}" \
			 --data-urlencode "context=R" \
			 --data-urlencode "comment=${logtext}" \
			 --data-urlencode "hostname=$HOSTNAME" \
			http://raspberrypi2.nyave:5000/insert/checklog)

	echo "Log Result: $result"
fi
