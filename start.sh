#!/bin/bash
echo 'start wechat.. '
echo "$1"

if [ "$1" == "s1" ]
then 
nohup python wechat.py 2>/dev/null 1>/dev/null&
fi

if [ "$1" == "s2" ]
then 
nohup python celery -A auto_tasks worker -l info -B 2>/dev/null 1>/dev/null&
fi


if [ "$1" == "h" ]
then 
#nohup python wechat.py 2>/dev/null&
echo "h: help info"
echo "s1: start wechat.py"
echo "s2: start celery task"
fi




echo 'start success!'

