#!/bin/bash
<<<<<<< HEAD
ROOT_DIR='/home/djangoprojects/freeports'
PID_FILE='/tmp/freeports_server.pid'
case "$1" in
    "start")
        find $ROOT_DIR -name "*.pyc" -exec rm '{}' \; 
        python2 manage.py runfcgi method=prefork host=127.0.0.1 port=8882 pidfile=$PID_FILE
=======
ROOT_DIR='/home/djangoprojects/test/freeports'
PID_FILE='/tmp/freeports_test_server.pid'
case "$1" in
    "start")
        find $ROOT_DIR -name "*.pyc" -exec rm '{}' \; 
        python2 manage.py runfcgi method=prefork host=127.0.0.1 port=8888 pidfile=$PID_FILE
>>>>>>> 813c2c8bfeb7b3f7b2bdc2a44418f72c0d698da8
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
