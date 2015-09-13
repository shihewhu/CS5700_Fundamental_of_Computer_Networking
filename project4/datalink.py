import socket, sys
import binascii
from struct import *
import commands
import subprocess
import re

# the default ethernet interface is eth0
NET_INTERFACE = 'eth0'

# assemble and disassemble Ethernet packet
class EtherPacket:
    def __init__(self):
        self.src_mac_addr = ''
        self.dest_mac_addr = ''
        self.ethernet_type = 0
        self.data = ''

    def assemble(self, ether_type = 0x800):
        # the default ethernet type is 0x800
        src = binascii.unhexlify(self.src_mac_addr)
        dest = binascii.unhexlify(self.dest_mac_addr)
        header = pack('!6s6sH', dest, src, ether_type)
        return header + self.data

    def disassemble(self, packet):
        # get the ethernet header and parse the src mac address and dest mac address
        [self.dest_mac_addr, self.src_mac_addr, self.ethernet_type] = unpack('!6s6sH', packet[:14])
        self.dest_mac_addr = binascii.hexlify(self.dest_mac_addr)
        self.src_mac_addr = binascii.hexlify(self.src_mac_addr)
        
        # get the payload of the packet, the length of ethernet header is 14 bytes
        self.data = packet[14:]

# ARP(Address Resolution Protocol) is used to find the dest mac address
class ARPPacket:
    def __init__(self):
        # type of hardware, 1 for ethernet
        self.hw_type = 1
        # type of protocol, default is ip
        self.proto_type = 0x800
        # length of hardware address 
        self.hw_addr_len = 6
        # length of ip address
        self.proto_addr_len = 4
        # operation: 1 for request, 2 for reply
        self.op = 0
        # sender hardware address
        self.send_hw_addr = ''
        # sender protocol address
        self.send_proto_addr = ''
        # receiver hardware address
        self.recv_hw_addr = ''
        # recevier protocol address
        self.recv_proto_addr = ''

    def assemble(self, operation = 1):
        # convert MAC address and IP address to binary format
        bin_SHA = binascii.unhexlify(self.send_hw_addr)
        bin_RHA = binascii.unhexlify(self.recv_hw_addr)
        bin_SPA = socket.inet_aton(self.send_proto_addr)
        bin_RPA = socket.inet_aton(self.recv_proto_addr)

        return pack("!HHBBH6s4s6s4s", self.hw_type, self.proto_type, self.hw_addr_len, self.proto_addr_len, \
                 operation, bin_SHA, bin_SPA, bin_RHA, bin_RPA)

    def disassemble(self, raw_packet):
        [self.hw_type, self.proto_type, self.hw_addr_len, self.proto_addr_len, self.op, bin_SHA, bin_SPA, \
        bin_RHA, bin_RPA] = unpack("!HHBBH6s4s6s4s", raw_packet)

        # parse the hardware address and protocol address
        self.send_hw_addr = binascii.hexlify(bin_SHA)
        self.recv_hw_addr = binascii.hexlify(bin_RHA)
        self.send_proto_addr = socket.inet_ntoa(bin_SPA)
        self.recv_proto_addr = socket.inet_ntoa(bin_RPA)

# DataLink layer
class DataLinkSocket:
    def __init__(self):
        self.src_mac = ""
        self.dest_mac = ""
        self.gateway_mac = ""
        # initiate two raw sockets, one for sending, the other for receving
        self.send_sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW)
        self.recv_sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(0x0800))

    def connect(self):
        # connect the sender and receiver
        self.send_sock.bind((NET_INTERFACE, 0))

    def get_mac_addr_by_arp(self, dest_ip):
        # build raw socket
        temp_send_sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW)
        # 0x0806 means arp protocol here
        temp_recv_sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(0x0806))

        # get the ip and mac address by helper function provided in the class
        src_mac = self.get_mac_addr(NET_INTERFACE)
        src_ip = self.get_ip_addr(NET_INTERFACE)
        # Set the MAC address to the socket for later comparison
        self.src_mac = src_mac

        # initiate a ARP packet, by seting its mac addr and ip addr
        arp_req_pkt = ARPPacket()
        arp_req_pkt.send_hw_addr = src_mac
        arp_req_pkt.send_proto_addr = src_ip

        # store the dest address, do boradcast
        arp_req_pkt.recv_hw_addr = "000000000000"
        arp_req_pkt.recv_proto_addr = dest_ip

        # initiate a ethernet packet
        ether_pkt = EtherPacket()
        ether_pkt.src_mac_addr = src_mac
        ether_pkt.dest_mac_addr = "FFFFFFFFFFFF"
        # 1 for request
        ether_pkt.data = arp_req_pkt.assemble(1) 

        # send packet to get Destination MAC Address, ARP is 0x0806 (default)
        temp_send_sock.sendto(ether_pkt.assemble(0x0806), (NET_INTERFACE, 0))

        # initiate a ethernet packet for sending for storing the parsed data from raw pkt
        arp_res_pkt = ARPPacket()
        while True:
            # Get raw data
            raw_pkt = temp_recv_sock.recvfrom(4096)[0]
            # disassemble the raw pkt received
            ether_pkt.disassemble(raw_pkt)
            if self.src_mac == ether_pkt.dest_mac_addr:
                # Disassemble the header
                arp_res_pkt.disassemble(ether_pkt.data[:28])
                if arp_res_pkt.recv_proto_addr == src_ip and arp_res_pkt.send_proto_addr == dest_ip:
                    break

        # close the scoket
        temp_send_sock.close()
        temp_recv_sock.close()
        # find the address and return 
        return arp_res_pkt.send_hw_addr

    def get_gateway_ip(self):
        # helper function for finding the gateway ip of local machine by commands 'route'
        out = subprocess.check_output(['route', '-n']).split('\n')
        data = []
        res = []

        for line in out:
            # get the line contains the gateway ip
            if line[:7] == '0.0.0.0':
                data = line.split(' ')
                break

        for i in range(len(data)):
            if data[i] != '':
                # append all the data which is not ' '
                res.append(data[i])

        # res[1] is the ip of gateway of the local machine
        return res[1]

    def get_mac_addr(self, interface = NET_INTERFACE):
        # helper function for finding the mac address of the local machine by commands 'ifconfig'
        ip_config = commands.getoutput("/sbin/ifconfig")

        # find the mac address in the ifconfig info
        mac_address_candidate = re.findall("HWaddr (.*?) ", ip_config)

        # remove all the ':' in the result
        return mac_address_candidate[0].replace(":", "")


    def get_ip_addr(self, interface = NET_INTERFACE):
        # helper function for finding the ip address of the local machine by commands 'ifconfig'
        ip_config = commands.getoutput("/sbin/ifconfig")

        # find the ip address in the ifconfig info
        ip_address_candidate = re.findall("inet addr:(.*?) ", ip_config)
        for ip in ip_address_candidate:
            # remove the local machine ip : 127.0.0.1
            if ip != '127.0.0.1':
                return ip

    def send(self, raw_packet):
        # build connection first
        self.connect()

        # get the gateway mac address
        if self.gateway_mac == '':
            try:
                self.gateway_mac = self.get_mac_addr_by_arp(self.get_gateway_ip())
            except:
                print 'ARP Fails, can not find mac address'
                sys.exit(0)

        # initiate a ethernet packet for sending 
        pkt = EtherPacket()
        pkt.src_mac_addr = self.src_mac
        # let the dest mac address be the mac address of gateway
        pkt.dest_mac_addr = self.gateway_mac
        self.dest_mac = pkt.dest_mac_addr
        pkt.data = raw_packet
        # send the ethernet packet out to the destination
        self.send_sock.send(pkt.assemble())

    def receive(self):
        # initiate the ethernet packet for receving
        pkt = EtherPacket()
        # Keep receiving, until received all 
        while True:
            # set the buffer to be 4096, and get the data only by using raw socket
            try:
                packet_recv = self.recv_sock.recvfrom(4096)[0]
            except socket.error:
                print 'socket recv maybe something wrong [Resource temporarily unavailable]'

            # disassemble the packet
            pkt.disassemble(packet_recv)

            # if the pakect's destination mac address equals to the socket's source mac address,
            # it means receive successfully
            if pkt.dest_mac_addr == self.src_mac and pkt.src_mac_addr == self.dest_mac:
                # the ethernet header has been removed
                return pkt.data