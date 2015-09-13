#!/bin/bash

username="$1"
echo $username
keyfile="$2"
ec2hosts=($(cut -d$'\t' -f1 ec2-hosts.txt))

# echo $ec2hosts
unset ec2hosts[0]

for h in ${ec2hosts[@]}; do
	echo delete cache on $h
	ssh -t -oStrictHostKeyChecking=no -i $keyfile $username@$h << ENDSSH &> /dev/null
	rm -r cache 
	rm *.pyc >> /dev/null
ENDSSH
don

echo delete cache on cs5700cdnproject
ssh -t -oStrictHostKeyChecking=no -i $keyfile $username@cs5700cdnproject.ccs.neu.edu << ENDSSH &> /dev/null
	rm cache.json
	rm *.pyc
ENDSSH
