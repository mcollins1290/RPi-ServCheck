#!/bin/bash
LOGTOSQL=true

cd "$(dirname "$0")";
./RPi-ServCheck.py F > ./Log/hourly-log 2>&1
retVal=$?

if [ "$LOGTOSQL" = true ] ; then
	logtext=$(cat ./Log/hourly-log)
	echo 'Logging to Pi Health Check MariaDB enabled'
	result=$(curl --silent -G --data-urlencode "code=SERV" \
			 --data-urlencode "status=${retVal}" \
			 --data-urlencode "context=H" \
			 --data-urlencode "comment=${logtext}" \
			 --data-urlencode "hostname=$HOSTNAME" \
			http://localhost:5000/insert/checklog)
		echo "Log Result: $result"
fi

exit $retVal
