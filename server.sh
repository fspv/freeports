#!/bin/bash
case "$1" in
    "start")
        find /home/djprogects/freeports -name "*.pyc" -exec rm '{}' \; 
<<<<<<< HEAD
        python2 manage.py runfcgi method=prefork host=127.0.0.1 port=8882 pidfile=/tmp/server.pid 
=======
        python2 manage.py runfcgi method=prefork host=127.0.0.1 port=8881 pidfile=/tmp/server.pid 
>>>>>>> ed587351429901d440c5f2ddc4c716fff5466c81
    ;;
    "stop") 
        kill -9 `cat /tmp/server.pid`
       rm /tmp/server.pid 
    ;;
    "restart")
        $0 stop
        sleep 1
        $0 start
    ;;
    *) echo "Usage: ./server.sh {start|stop|restart}";;
esac
