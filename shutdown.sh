#!/bin/bash

echo 'shutdown wechat process...'
a=(`ps -ef | grep wechat | awk '{print $2}'`)
b=${#a[*]}
echo $b

idx=0
for i in ${a[@]}
do
kill "$i"
echo "killprocess pid=$i"
done

echo "finish!"



