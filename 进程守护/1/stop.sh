#!/bin/sh
ps -ef | grep "python3" | awk '{print $2}' | xargs kill -s 9
