#!/bin/bash

file="$1"

cat $file | sort  >> serverRecord
cat $file | grep "Asia Pacific Network Information Centre" | awk -F $'\t' '{print $1}' | sort | uniq | while read line; 
do echo "$line	$(whois $line | grep netname | sed 's/   */	/g' | cut -f2)"; done | sort >> serverRecord
cat serverRecord | sort >> serverContacted