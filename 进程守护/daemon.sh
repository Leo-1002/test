while true;
do
        server=`ps aux | grep test| grep -v grep`
        if [ ! "$server" ]; then
           cd 目录
           nohup java -jar -XX:PermSize=128m -Xms1024m -Xmx1024m test.jar &
        fi
        sleep 5
done

#nohup ./daemon.sh &