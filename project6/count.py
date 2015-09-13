f = open("serverRecord", 'r'):
count = {}
while f:
	line = f.readline()
	if line != '' and 'Internet Assigned Numbers Authority' not in line and 'Asia Pacific Network Information Centre' not in line and 'data//tcpdump' not in line:
		ip_name = line.split()
		if len(ip_name) == 2:
			if ip_name[1] not in count.keys():
				count[ip_name[1]] = 1
			else:
				count[ip_name[1]] += 1
f = open("serverRecordCount", 'w')
for key in count:
	f.write(str(count[key]) + " " + key)

