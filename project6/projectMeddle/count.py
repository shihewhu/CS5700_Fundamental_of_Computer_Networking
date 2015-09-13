# open file to parse
f = open("serverContacted", 'r')
count = {}
line = f.readline()
while line:
	# read a line
	line = f.readline()
	if line != '' and 'Internet Assigned Numbers Authority' not in line and 'Asia Pacific Network Information Centre' not in line and 'data//tcpdump' not in line:
		# get the severname
		ip_name = line.split()
		if len(ip_name) != 2:
			ip_name = line.split('\t')
		if len(ip_name) != 2 or ip_name[1] == '\n':
			continue
		if len(ip_name) == 2:
			print ip_name
			# count the server in a dict
			if ip_name[1] not in count.keys():

				count[ip_name[1]] = 1
			else:
				count[ip_name[1]] += 1
f = open("serverRecordCount", 'w')
for key in count:
	if "\n" not in key:
		f.write(str(count[key]) + " " + key + "\n")
	else:
		f.write(str(count[key]) + " " + key)


