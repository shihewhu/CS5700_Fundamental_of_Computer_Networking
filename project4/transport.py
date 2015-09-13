#####################################################################
# some package imported
#####################################################################
import socket, sys
from struct import *
import re
import commands
import urlparse
from random import randint
import time
from network import IpPacket, IpSocket
import array
#####################################################################
# global constant
#####################################################################
BUFF = 65535
MAX_TIMEOUT = 60 # one min
#####################################################################
# checksum function : tcp_packet with checksum 0 -> a checksum number 
# for integrity valiation
# define checksum function for detecting the correctness of checksum

def checksum(s):
	if len(s) & 1:
		s = s + '\0'
	words = array.array('h', s)
	sum = 0
	for word in words:
		sum = sum + (word & 0xffff)
	hi = sum >> 16
	lo = sum & 0xffff
	sum = hi + lo
	sum = sum + (sum >> 16)
	return (~sum) & 0xffff

#####################################################################
# _get_local_host : None -> the ip of this machine
# get the host ip address of the local machine
#####################################################################
def _get_local_host():
	ip_config = commands.getoutput("/sbin/ifconfig") # print the ifconfig
	# find the ip address in the ifconfig info
	ip_address_candidate = re.findall("inet addr:(.*?) ", ip_config)
	# print ip_address_candidate
	for ip in ip_address_candidate:
		if ip != '127.0.0.1':
			return ip
####################################################################
# _get_port : None -> the random port number
# generate random port number
####################################################################
def _get_port():
	return randint(30000, 65565)

####################################################################
# a class which defines tcp packet object. The attributes are the signature
# of the header and data. Each tcp packet has its own wrap method and unwrap
# method. The wrap method return a encoded tcp packet using all the attributes
# The unwrap method decodes a tcp packet and gets all the attributes
####################################################################
# attributes
####################################################################
class TcpPacket:
	def __init__(self, src_port_ = 0, dest_port_ = 0, src_ip_ = '', dest_ip_ = '', data_ = ''):
		self.src_port = src_port_
		self.dest_port = dest_port_
		self.seq_num = 0
		self.ack_num = 0
		self.data_off = 5
		self.fin = 0
		self.syn = 0
		self.rst = 0
		self.psh = 0
		self.ack = 0
		self.urg = 0
		self.window = 65535
		self.checksum = 0
		self.urg_ptr = 0
		self.data = data_
		self.src_ip = src_ip_
		self.dest_ip = dest_ip_
		self.MSS = 536
	###############################################################
	# wrap : None -> encoded tcp packet
	###############################################################
	def wrap(self):
		# change the dot format to 32-bit format
		src_ip = socket.inet_aton(self.src_ip)
		dest_ip = socket.inet_aton(self.dest_ip)
		self.checksum = 0
		offset_res = (self.data_off << 4) + 0
		tcp_flags = self.fin + (self.syn << 1) + (self.rst << 2) + (self.psh << 3) + (self.ack << 4) + (self.urg << 5)
		# return a string according to the given format !HHLLBBHHH
		tcp_header = pack('!HHLLBBHHH', self.src_port, self.dest_port, self.seq_num, \
			self.ack_num, offset_res, tcp_flags, self.window, self.checksum, self.urg_ptr)

		placeholder = 0
		protocol = socket.IPPROTO_TCP
		tcp_length = len(tcp_header) + len(self.data)
		# return a string according to the given format '!4s4sBBH'
		pesudo_header = pack('!4s4sBBH', src_ip, dest_ip, placeholder, protocol, tcp_length)
		temp = pesudo_header + tcp_header + self.data
        # do the checksum 
		if len(temp) % 2 != 0:
			temp = temp + pack('B', 0)
		self.checksum = checksum(temp)

		# return a string representing the tcp header
		tcp_header_new = pack('!HHLLBBH', self.src_port, self.dest_port, self.seq_num, self.ack_num, \
			offset_res, tcp_flags, self.window) + pack('H', self.checksum) + pack('!H', self.urg_ptr)

		# assemble the packet
		return tcp_header_new + self.data
	###############################################################
	# unwrap : encoded tcp packet -> None
	###############################################################
	def unwrap(self, packet_raw):
		# disassemble the packet
		[self.src_port, self.dest_port, self.seq_num, self.ack_num, offset_res, tcp_flags,
		self.window] = unpack('!HHLLBBH', packet_raw[0:16])
		[self.checksum] = unpack('H', packet_raw[16:18])
		[self.urg_ptr] = unpack('!H', packet_raw[18:20])

		len_header = offset_res >> 4
		self.fin = tcp_flags & 0x01
		self.syn = (tcp_flags & 0x02) >> 1
		self.rst = (tcp_flags & 0x04) >> 2
		self.psh = (tcp_flags & 0x08) >> 3
		self.ack = (tcp_flags & 0x16) >> 4
		self.urg = (tcp_flags & 0x32) >> 5
		self.data = packet_raw[len_header * 4:]
		# do the checksum
		# 1. set the pesudo header
		src_ip = socket.inet_aton(self.src_ip)
		dest_ip = socket.inet_aton(self.dest_ip)
		placeholder = 0
		protocol = socket.IPPROTO_TCP
		# tcp_length should be the length inside the header * 4 and plust the length of the data
		tcp_length = len_header*4+len(self.data)
		
		pesudo_header = pack('!4s4sBBH', src_ip, dest_ip, placeholder, protocol, tcp_length)
		tcp_header_and_data = packet_raw[:16]  + pack('H', 0) + packet_raw[18:]
		temp = pesudo_header + tcp_header_and_data
		new_checksum = checksum(temp)
		# receive the wrong packet
		if self.checksum != new_checksum:
			raise ValueError


################################################################
# class of a tcp socket object. Each tcp socket object has
# these attributes. Each tcp object provides connect(three way handshake)
# send, recvall and close(tear down the connection)
# Once instantiating a tcp socket, the program can use this tcp socket
# to connect to the server and send, receive the messages. 
################################################################
class TcpSocket:
 	def __init__(self, src_ip_ = '', dest_ip_ = '', data_ = ''):
 		self.src_ip = src_ip_
 		self.dest_ip = dest_ip_
 		self.src_port = 0
 		self.dest_port = 0
 		self.seq_num = 0
 		self.ack_num = 0
 		# use the socket provided by network layer
 		self.sock = IpSocket()
 		self.pre_seq = 0 # to store the packet seq and ack number for retransmission
		self.pre_ack = 0
		self.cwnd = 1 # the congestion window used to congestion control
		self.MSS = 536
 	##########################################################
 	# connect : hostname, dest_port -> None
 	# This method does the three way handshake and store the final
 	# ack num and seq num for sending data and receiving data
 	##########################################################
 	def connect(self, hostname, dest_port = 80):

 		self.dest_port = dest_port
 		src_ip_ = _get_local_host()
 		dest_ip_ = socket.gethostbyname(hostname)
 		self.dest_ip = dest_ip_
 		self.src_ip = src_ip_
 		self.src_port = _get_port() # here we can randomly pick one, but I'm not sure whether it is correct
 		
 		# new a packet and start the three way hand shake
 		self.data = ''
 		tcp_packet = TcpPacket(self.src_port, self.dest_port, self.src_ip, self.dest_ip, self.data)
 		tcp_packet.syn = 1
 		# generate sequence number randomly
 		self.seq_num = randint(0, 65535)
 		# tcp_packet.set_seq_num(self.seq_num)
 		tcp_packet.seq_num = self.seq_num
 		count = 0
 		while True:
 			if count >= 3:
	 			print "no response for 3 min, exit"
	 			sys.exit(0)
	 		self._send(tcp_packet.wrap())
	 		tcp_packet = self._recv_until_timeout()
	 		# raw_packet = self.sock.recv()
	 		if tcp_packet == '' and count < 3:
	 			count += 1
	 			print count
	 			continue
	 		if tcp_packet.rst == 1:
	 			print "error due to reset"
	 			sys.exit(0)
	 		else:
	 			# receive the ack msg from server successfully
	 			if tcp_packet.syn == 1 and tcp_packet.ack == 1 and tcp_packet.ack_num == self.seq_num + 1:
	 				self.seq_num = tcp_packet.ack_num
	 				self.ack_num = tcp_packet.seq_num
	 				break
	 			else:
	 				count += 1
	 				print count
	 				continue

 		tcp_packet = TcpPacket(self.src_port, self.dest_port, self.src_ip, self.dest_ip, self.data)
 		tcp_packet.ack = 1
 		tcp_packet.seq_num = self.seq_num
 		tcp_packet.ack_num = self.ack_num + 1
 		self.ack_num = self.ack_num + 1
 		self._send(tcp_packet.wrap())
 		# til now, three way shakes finished

 	##########################################################
 	# send : data -> None
 	# This method is used to send data to the server using the 
 	# the seq number and ack number stored at the end of the 
 	# three handshake or other part. This method implements 
 	# congestion control. Also, it will wait for the ack for the
 	# data sent. After for 1 minute, it will resend the data. And
 	# if for 3 mintues no response, the program will exit
 	##########################################################
 	def send(self, data):
 		# build a new tcp packet and send it to the dest ip, then wait for the ack. 
 		# If the wait time exceeds the timeout, retransmit this packet
 		# slow start
 		self.cwnd = self.MSS
 		while len(data) > 0:
 			send_data = data[:self.cwnd]
 			data = data[self.cwnd:]
	 		tcp_packet = TcpPacket(self.src_port, self.dest_port, self.src_ip, self.dest_ip, data)
	 		tcp_packet.seq_num = self.seq_num
	 		tcp_packet.ack_num = self.ack_num
	 		tcp_packet.ack = 1
	 		tcp_packet.psh = 1
	 		tcp_packet.data = send_data
	 		# send the packet out using the send method provided by network layer

	 		self._send(tcp_packet.wrap())
	 		# receive process 
	 		while True:
		 		tcp_packet_receive = self._recv_until_timeout()
		 		if tcp_packet_receive == '':
		 			print "received ack errors"
		 			tcp_packet_retrans = TcpPacket(self.src_port, self.dest_port, self.src_ip, self.dest_ip, data)
		 			tcp_packet_retrans.seq_num = self.seq_num
		 			tcp_packet_retrans.ack_num = self.ack_num
		 			tcp_packet_retrans.ack = 1
		 			tcp_packet_retrans.psh = 1
		 			# can't receive the ack, decrease the cwnd
		 			if self.cwnd > 1:
		 				self.cwnd /= 2
		 			else:
		 				self.cwnd = self.MSS
		 			tcp_packet_retrans.data = send_data
		 			try:
		 				self._send(tcp_packet_retrans.wrap())
		 			except:
		 				continue
		 			# tcp_packet.reset()
		 		else:
		 			# filter the packet, the packet we want should be a ack packet
		 			# and the ack num should be the seq_num we send + data size(the next seq_num the 
		 			# receiver wants)
					# print tcp_packet_receive.ack_num, self.seq_num + min(self.cwnd, len(send_data))
		 			if tcp_packet_receive.rst == 1:
		 				print "error due to reset"
		 				sys.exit(0)
		 			if tcp_packet_receive.ack == 1 and tcp_packet_receive.ack_num == (self.seq_num + min(self.cwnd, len(send_data))):
		 				# succeeds receiving ack, increase the cwnd
		 				self.cwnd *= 2
		 				self.pre_ack = self.ack_num
		 				self.pre_seq = self.seq_num
		 				self.seq_num = tcp_packet_receive.ack_num
		 				self.ack_num = tcp_packet_receive.seq_num
		 				
		 				# self.data = data
		 				break
		 			else:
		 				continue

 	##########################################################
 	# recv_all : None -> data
 	# This method is used to receive the data sent from the server
 	# It will check the seq number of the data received and tell
 	# whether it is the packet previously acked. If not, this metod
 	# will request for the retransmission. The method will continue
 	# receiving the data until the server sends the fin for tearing
 	# down the connection.
 	##########################################################

 	def recv_all(self):
 		result_data = []
 		# ack_count = 0
 		while True:
	 		tcp_packet = self._recv_until_timeout()
	 		# timeout, nothing get, exit the program
	 		if tcp_packet == '':
	 			print "received errors"
	 			sys.exit(0)
	 		# if we receive a reset packet, the connection is done, exit the program
	 		if tcp_packet.rst == 1:
	 			print "received errors"
	 			sys.exit(0)
	 		else:
	 			# check the seq number, if it is the packet we want, ack new packet
	 			# otherwise request for retransmission
	 			if tcp_packet.seq_num == self.pre_ack:
	 				# If the server sends the finish packet, ack this finish packet
	 				# and ends the receiving process
		 			if tcp_packet.fin == 1 :	
		 				self.ack_num = tcp_packet.seq_num + len(tcp_packet.data) + 1
		 				self.seq_num = tcp_packet.ack_num
		 				tcp_packet_for_ack_fin = TcpPacket(self.src_port, self.dest_port, self.src_ip, self.dest_ip, '')
			 			tcp_packet_for_ack_fin.ack = 1
			 			tcp_packet_for_ack_fin.ack_num = self.ack_num
			 			tcp_packet_for_ack_fin.seq_num = self.seq_num
			 			self._send(tcp_packet_for_ack_fin.wrap())
			 			self.pre_ack = self.ack_num
			 			self.pre_seq = self.seq_num
		 				break
		 			# if the packet is not a finished pacekt, continue reveiving the data
		 			else:
		 				result_data.append(tcp_packet.data)
		 				self.seq_num = tcp_packet.ack_num
		 				self.ack_num = tcp_packet.seq_num + len(tcp_packet.data)
		 				tcp_packet_for_ack_next = TcpPacket(self.src_port, self.dest_port, self.src_ip, self.dest_ip, '')
		 				tcp_packet_for_ack_next.ack = 1
		 				tcp_packet_for_ack_next.seq_num = self.seq_num
		 				tcp_packet_for_ack_next.ack_num = self.ack_num
			 			self._send(tcp_packet_for_ack_next.wrap())
			 			self.pre_seq = self.seq_num
			 			self.pre_ack = self.ack_num
			 	# If the received packet is wrong, do retransmission process
	 			elif tcp_packet.seq_num != self.pre_ack:
		 			tcp_packet_ack_loss_packet = TcpPacket(self.src_port, self.dest_port, self.src_ip, self.dest_ip, '')
		 			tcp_packet_ack_loss_packet.ack_num = self.pre_ack
		 			tcp_packet_ack_loss_packet.seq_num = self.pre_seq
		 			tcp_packet_ack_loss_packet.ack = 1
	 				self._send(tcp_packet_ack_loss_packet.wrap())

	 	return ''.join(result_data)
	##########################################################
 	# close : None -> None
 	# This method is used to finish a connection. First, it will
 	# send the fin+ack packet to the server. If no response, exit
 	# the method, if the server sends the fin+ack, it will send
 	# the ack as well.
 	##########################################################
	def close(self):
		# send the fin+ack packet to the server
		tcp_packet_for_fin = TcpPacket(self.src_port, self.dest_port, self.src_ip, self.dest_ip, '')
		tcp_packet_for_fin.fin = 1
		tcp_packet_for_fin.ack = 1
		tcp_packet_for_fin.ack_num = self.ack_num
		tcp_packet_for_fin.seq_num = self.seq_num
		self._send(tcp_packet_for_fin.wrap())
		# wait for the response
		tcp_packet = self._recv_until_timeout()
		# timeout and no response, exit 
		if tcp_packet == '':
			print 'can\'t receive ack, client finishes itself'
			sys.exit(0)
		# get a reset packet, exit
		if tcp_packet.rst == 1:
			print "error due to reset"
			sys.exit(0)
		else:
			# received a fin+ack packet, send the ack packet to server and ends the close method
			if self.ack_num == tcp_packet.seq_num and self.seq_num + 1== tcp_packet.ack_num and tcp_packet.fin == 1 and tcp_packet.ack == 1:
				print "correct"
				self.ack_num = tcp_packet.seq_num + 1
				self.seq_num = tcp_packet.ack_num
				tcp_packet = TcpPacket(self.src_port, self.dest_port, self.src_ip, self.dest_ip, '')
				tcp_packet.ack_num = self.ack_num
				tcp_packet.seq_num = self.seq_num
				tcp_packet.fin = 1
				self._send(tcp_packet.wrap())
				return 
			# received a ack packet, end the close method
			elif self.ack_num == tcp_packet.seq_num and self.seq_num + 1== tcp_packet.ack_num and tcp_packet.ack == 1 and tcp_packet.fin == 0:
				# print "finish"
				return 
			else:
				print "some error happens"
				sys.exit(0)
	######################################################
	# _send : encoded tcp_packet -> None
	# This method is a private method for sending data use the
	# socket provided by the network layer. It will contiune
	# trying to send the data until it succeeds or 10 times 
	######################################################
	def _send(self, tcp_packet):
 		count = 0
 		while True:
 			try:
 				self.sock.send(self.src_ip, self.dest_ip, tcp_packet)
 				break
 			except:
 				if count > 10:
 					print "some errors happens, please check you device and try again"
 					sys.exit(0)
 				count += 1
 				continue
 	######################################################
 	# _recv_until_timeout : None -> tcp packet object
	# This method is a private method for receiving the data
	# it will contiune trying to receive the right tcp packet
	# until it succeeds or time out 
	#######################################################
 	def _recv_until_timeout(self):
 		start = time.time()
 		tcp_packet = TcpPacket()
 		while time.time() - start < MAX_TIMEOUT:
 			# try the recv() method provided network layer
 			try:
 				raw_packet = self.sock.recv(socket.IPPROTO_TCP)
 			except:
 				continue
 			# do the checksum 
 			tcp_packet.src_ip = self.dest_ip
			tcp_packet.dest_ip = self.src_ip
 			try:
 				tcp_packet.unwrap(raw_packet)
 			except ValueError:
 				continue
 			# if the packet port is correct, return the tcp packet object-
 			if tcp_packet.src_port == self.dest_port and tcp_packet.dest_port == self.src_port:
 				return tcp_packet
 			else:
 				continue
 		return ''
