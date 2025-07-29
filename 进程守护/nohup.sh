#!/bin/bash
 
sleep 10        
 
while true;
do
    variable=`ps aux | grep helloworld | grep -v grep`    # helloworld 是程序名字
    if [ ! "$variable" ]; then
        cd /home/ygt/test/
        nohup ./helloworld &
        echo 'restart helloworld at time' >> restart_log.txt
        echo $(date +%F%n%T) >> restart_log.txt
    fi
 
    sleep 10    # 每10秒监测一次
done