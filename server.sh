#!/bin/bash
ROOT_DIR='/home/djangoprojects/freeports'
PID_FILE='/tmp/freeports_server.pid'
case "$1" in
    "start")
        find $ROOT_DIR -name "*.pyc" -exec rm '{}' \; 
        python2 manage.py runfcgi method=prefork host=127.0.0.1 port=8882 pidfile=$PID_FILE
		echo "[$(cat $PID_FILE)] running"	
    ;;
    "stop") 
		kill -9 $(cat $PID_FILE)
   		rm $PID_FILE 2>/dev/null
    ;;
    "restart")
        $0 stop
        sleep 1
        $0 start
    ;;
    *) echo "Usage: ./server.sh {start|stop|restart}";;
esac
