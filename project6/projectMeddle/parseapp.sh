#!/bin/bash

file="$1"
# sort the file and store them into tmp file
cat $file | sort  >> serverRecord
# query all the ip belonging to  the Asia Pacific Network Information Centre. and store them into tmp file
cat $file | grep "Asia Pacific Network Information Centre" | awk -F $'\t' '{print $1}' | sort | uniq | while read line; 
do echo "$line	$(whois $line | grep netname | sed 's/   */	/g' | cut -f2)"; done | sort >> serverRecord
# sort the tmp file and redirect all the dat into serverContacted file.
cat serverRecord | sort >> serverContacted