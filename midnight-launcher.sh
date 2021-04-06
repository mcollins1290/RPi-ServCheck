#!/bin/bash
LOGTOSQL=true

cd "$(dirname "$0")";
./RPi-ServCheck.py T > ./Log/midnight-log 2>&1
retVal=$?

if [ "$LOGTOSQL" = true ] ; then
	logtext=$(cat ./Log/midnight-log)
	echo 'Logging to Pi Health Check MariaDB enabled'
	result=$(curl -G --data-urlencode "code=SERV" \
			 --data-urlencode "status=${retVal}" \
			 --data-urlencode "context=D" \
			 --data-urlencode "comment=${logtext}" \
			 --data-urlencode "hostname=$HOSTNAME" \
			http://raspberrypi2.nyave:5000/insert/checklog)

	echo "Log Result: $result"
fi
