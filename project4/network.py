#####################################################################
# some package imported
#####################################################################
import socket
import array
from datalink import DataLinkSocket
from struct import *
from random import randint

####################################################################
# network_chksum : tcp packet with checksum 0 -> checksum value
# This function is the global function used to calculate the checksum
####################################################################
def network_chksum(msg):
    if len(msg) & 1:
        msg = msg + '\0'
    words = array.array('h', msg)
    sum = 0
    for word in words:
        sum = sum + (word & 0xffff)
    high = sum >> 16
    low = sum & 0xffff
    sum = high + low
    sum = sum + (sum >> 16)
    return (~sum) & 0xffff

####################################################################
# This class is used to define the ip packet. It has the attributes of
# all the signatures inside the ip header. Each ip packet object has 
# two method, wrap and unwrap. The wrap method wrap all the atrributes 
# and encode and return a ip packet for sending. The unwrap method
# takes an encoded ip packet and disassmable it and return the ip packet
# object
###################################################################
class IpPacket:
	def __init__(self, saddr_ = '', daddr_ = '', data_ = ''):
		self.ip_ihl = 5 
		self.ip_ver = 4 # ipv4
		self.ip_tos = 0
		self.ip_ecn = 0
		self.ip_tot_len = 0 # length of the packet, kernel will fill the correct total length
		self.ip_id = 0 # need to revise
		self.ip_flag_df = 1 # do not fragment
		self.ip_flag_mf = 0
		self.ip_frag_off = 0
		self.ip_ttl = 255 # time to live defalut with 255
		self.ip_proto = socket.IPPROTO_TCP # TCP protocol
		self.ip_check = 0 # the ip check sum
		self.ip_saddr = saddr_ # what is inet_aton, need to check, if we use raw socket, we can spoof this feild
		self.ip_daddr = daddr_
		self.ip_ihl_ver = (self.ip_ver << 4) + self.ip_ihl
		self.ip_tos_ecn = (self.ip_tos << 2) + self.ip_ecn
		self.ip_flag_frag = (((self.ip_flag_df << 1) + self.ip_flag_mf) << 13) + self.ip_frag_off
		self.data = data_

	##############################################################
	# wrap : None -> encoded ip packet
	# This method takes all the attributes of the ip packet object and 
	# encode them into a ip packet for sending
	##############################################################
	def wrap(self):
		# assign id randomly
		self.id = randint(0, 65535)

		self.ip_tot_len = self.ip_ihl * 4 + len(self.data)
		
		# assign the src ip and dest ip address
		src_addr = socket.inet_aton(self.ip_saddr)
		dest_addr = socket.inet_aton(self.ip_daddr)

		# return a string packing according to the format !BBHHHBBH4s4s
		pesudo_ip_header = pack('!BBHHHBBH4s4s', self.ip_ihl_ver, self.ip_tos_ecn, self.ip_tot_len, \
			self.ip_id, self.ip_flag_frag, self.ip_ttl, self.ip_proto, self.ip_check, src_addr, dest_addr)

		# caculate the checksum
		self.ip_check = network_chksum(pesudo_ip_header)

		# assemble the packet again and return
		ip_header = pack('!BBHHHBB', self.ip_ihl_ver, self.ip_tos_ecn, self.ip_tot_len, \
			self.ip_id, self.ip_flag_frag, self.ip_ttl, self.ip_proto) + \
			pack('H', self.ip_check) + pack('!4s4s', src_addr, dest_addr)

		packet = ip_header + self.data
		return packet
	##############################################################
	# unwrap : encoded packet -> None
	# This method takes an encoded packet, and get all the attributes
	# inside the packet and set them to the attribute of an ip packet
	# object. It will do the checksum if the checksum is wrong, rasie
	# an exception for handling
	##############################################################
	def unwrap(self, packet_raw):
		# unpack according the format !BBHHHBBH4s4s
		[self.ip_ihl_ver, self.ip_tos_ecn, self.ip_tot_len, self.ip_id, self.ip_flag_frag, \
		self.ip_ttl, self.ip_proto] = unpack('!BBHHHBB', packet_raw[0:10])
		[self.ip_check] = unpack('H', packet_raw[10:12])
		[src_addr, dest_addr] = unpack('!4s4s', packet_raw[12:20])

		self.ip_ihl = self.ip_ihl_ver & 0x0f
		self.ip_ver = (self.ip_ihl_ver & 0xf0) >> 4
		self.ip_tos = (self.ip_tos_ecn & 0xfc) >> 2
		self.ip_ecn = self.ip_tos_ecn & 0x03
		self.ip_flag_df = (self.ip_flag_frag & 0x40) >> 14
		self.ip_flag_mf = (self.ip_flag_frag & 0x20) >> 13
		self.ip_frag_off = self.ip_flag_frag & 0x1f

		self.ip_saddr = socket.inet_ntoa(src_addr)
		self.ip_daddr = socket.inet_ntoa(dest_addr)
		# self.data = packet_raw[0][self.ip_ihl *4 : self.ip_tot_len]
		# get the data fromt the encoded packet by ip totoal length
		self.data = packet_raw[self.ip_ihl*4:self.ip_tot_len]

		# check the correctness of chksum
		pesudo_ip_header = packet_raw[0:10] + pack('H', 0) + packet_raw[12:20]
		new_chksum = network_chksum(pesudo_ip_header)
		if self.ip_check != new_chksum:
			raise ValueError
		
####################################################################
# This class for defining a ip socket object. It maintains a socket provided
# by the datalink layer for sending and receiving data. Each ip socket
# object has send and recv method. The socket will specify which type
# packet should received and filter all other packet.
###################################################################
class IpSocket:
	def __init__(self, saddr_ = '', daddr_ = ''):
		self.sock = DataLinkSocket()
		# self.buffer = 6000 # buffer size
		self.src_addr = saddr_ # soure ip address
		self.dest_addr = daddr_ # destination ip address
		# self.s_send = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
		# self.s_recv = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)	
	##############################################################
	# send : source ip address, destintation ip address, data -> None
	# This method is used to send data to destintaion ip address
	# it will create an ip packet object and wrap it into an encoded
	# packet and send it to dest ip address machine
	# if the sending process makes some errors, it will raise an exception
	##############################################################
	def send(self, saddr_, daddr_, data):
		self.src_addr = saddr_
		self.dest_addr = daddr_
		ip_packet_for_send = IpPacket(self.src_addr, self.dest_addr, data)
		try:
			self.sock.send(ip_packet_for_send.wrap())
		except:
			raise ValueError
		#self.s_send.sendto(ip_packet_for_send.wrap(), (self.dest_addr, 0))
	##############################################################
	# recv : the type of the packet expected to receive -> data
	# This method uses the socket provided by the datalink layer
	# to receive the packet. It will filter the packet by the 
	# ip address and packet type.
	##############################################################
	def recv(self, packet_type = socket.IPPROTO_TCP):	
		while True:
			ip_packet_received = IpPacket()
			packet_raw = self.sock.receive()
			# packet_raw = self.s_recv.recvfrom(self.buffer)
			try:
				ip_packet_received.unwrap(packet_raw)
			except:
				# print "IP checksum errors"
				# drop the ip_packet_received
				continue
			# filter the ip ip_packet_received by validing their source
			# addresses and destintation addresses.
			if ip_packet_received.ip_proto == packet_type and \
               ip_packet_received.ip_saddr == self.dest_addr and \
               ip_packet_received.ip_daddr == self.src_addr:
				return ip_packet_received.data