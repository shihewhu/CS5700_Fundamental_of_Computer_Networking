#!/bin/bash

directoryname="$1"
# filename="$"1"
tmp="$2"
outputpath="$3"
for filename in $directoryname/*.clr; do
	echo $filename >> $outputpath
	rm $tmp.txt
	echo "get tmp"
	tcpdump -Ar $filename| grep -v 'TCP' | grep -v 'HTTP' | grep -v 'seq' > $tmp.txt
	echo "loc search"
	egrep -io "[^a-zA-Z]?lat([^a-zA-Z]|itude).*[0-9]+(\.?)[0-9]+" $tmp.txt | sort | uniq -c >> $outputpath

	#echo " Looking for pw=, pwd=, password=, user= " #generalized password and username. commented out because we searched for phone-specific
	#egrep -io "[^a-zA-Z]?pw[^a-zA-Z]?([=:])+(\"?)....."> $tmp.txt | sort | uniq -c
	#egrep -io "[^a-zA-Z]?pwd[^a-zA-Z]?([:=])+(\"?)...."> $tmp.txt | sort | uniq -c
	#egrep -io "[^a-zA-Z]?password[^a-zA-Z]?([:=])+(\"?)...."> $tmp.txt | sort | uniq -c
	#egrep -io "[^a-zA-Z]?user[^a-zA-Z]?([:=])+(\"?)...."> $tmp.txt | sort | uniq -c

	#echo " Looking for IMEI=  " #generalized imei. commented out because we searched for phone specific.
	#egrep -io "[^a-zA-Z]?IMEI[^a-zA-Z]?([:=])+(\"?)[0-9]{15,}"> $tmp.txt | sort | uniq -c
	#egrep -io "[^a-zA-Z]?udid[^a-zA-Z]?([:=])+(\"?)[0-9]{15,}"> $tmp.txt | sort | uniq -c
	#egrep -io "[^a-zA-Z]?uuid[^a-zA-Z]?([:=])+(\"?)[0-9]{15,}"> $tmp.txt | sort | uniq -c
	#egrep -io "[^a-zA-Z]?-Id[^a-zA-Z]?([:=])+(\"?)[0-9]{15,}"> $tmp.txt | sort | uniq -c
	#phone-specific searches
	echo "IMEI"
	grep -i "XXXXXXXXXXXXXX" $tmp.txt | sort | uniq -c >> $outputpath

	# grep -i "355031040753366"> $tmp.txt | sort | uniq -c
	grep -i "XXXXXXXXXXXXXX" $tmp.txt | sort| uniq -c >> $outputpath

	grep -i "XXXXXXXXXXXXXX" $tmp.txt | sort | uniq -c >> $outputpath

	echo "contact info"
	#contact info (phone specific)
	grep -i "XXXXXXXXXXXXXX" $tmp.txt | sort | uniq -c >> $outputpath
	grep -i "XXXXXXXXXXXXXX" $tmp.txt | sort | uniq -c >> $outputpath
	grep -i "XXXXXXXXXXXXXX" $tmp.txt | sort | uniq -c >> $outputpath

	egrep -io "[^a-zA-Z]?number[^a-zA-Z]?([:=])+(\"?).........." $tmp.txt | sort | uniq -c >> $outputpath
	egrep -io "[^a-zA-Z]?phone[^a-zA-Z]?([:=])+(\"?)........." $tmp.txt | sort | uniq -c >> $outputpath

	echo "visa credit"
	egrep -io '4[0-9]{12}(?:[0-9]{3})?' $tmp.txt | sort  | uniq -c >> $outputpath #Visa 
	# # egrep -io '5[1-5][0-9]{14}"> $tmp.txt | sort | uniq -c #MasterCard
	# # egrep -io '[47][0-9]{13}"> $tmp.txt | sort | uniq -c #AmEx
	# # egrep -io '3(?:0[0-5]|[68][0-9])[0-9]{11}"> $tmp.txt | sort | uniq -c #DinersClub
	# # egrep -io '6(?:011|5[0-9]{2})[0-9]{12}"> $tmp.txt | sort | uniq -c #Discover
	# # egrep -io '(?:2131|1800|35\d{3})\d{11}"> $tmp.txt | sort | uniq -c #JCB
	echo "email"
	egrep -io "[^ ]+@([a-z]+\.)+(((com)|(org))|((edu)|(net)))" $tmp.txt >> $outputpath
done;