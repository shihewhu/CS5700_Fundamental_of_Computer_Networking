import socket
import array
from datalink import DataLinkSocket
from struct import (pack, unpack)
from random import randint

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


class IpPacket(object):
    def __init__(self, src_addr='', dest_addr='', data_=''):
        self.ip_ihl = 5
        self.ip_ver = 4 # ipv4
        self.ip_tos = 0
        self.ip_ecn = 0
        self.ip_tot_len = 0 # length of the packet, kernel will fill the correct total length
        self.ip_id = 0 # need to revise
        self.ip_flag_df = 1
        self.ip_flag_mf = 0
        self.ip_frag_off = 0
        self.ip_ttl = 255 # time to live defalut with 255
        self.ip_proto = socket.IPPROTO_TCP # TCP protocol
        self.ip_check = 0 # the ip check sum
        self.ip_saddr = src_addr # what is inet_aton, need to check, if we use raw socket, we can spoof this feild
        self.ip_daddr = dest_addr
        self.ip_ihl_ver = (self.ip_ver << 4) + self.ip_ihl
        self.ip_tos_ecn = (self.ip_tos << 2) + self.ip_ecn
        self.ip_flag_frag = (((self.ip_flag_df << 1) + self.ip_flag_mf) << 13) + self.ip_frag_off
        self.data = data_

    def wrap(self):
        self.id = randint(0, 65535)
        self.ip_tot_len = self.ip_ihl * 4 + len(self.data)
        src_addr = socket.inet_aton(self.ip_saddr)
        dest_addr = socket.inet_aton(self.ip_daddr)
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

    def unwrap(self, packet_raw):
        """unpack according the format !BBHHHBBH4s4s"""
        (self.ip_ihl_ver, self.ip_tos_ecn, self.ip_tot_len, self.ip_id, self.ip_flag_frag, \
        self.ip_ttl, self.ip_proto) = unpack('!BBHHHBB', packet_raw[0:10])
        (self.ip_check) = unpack('H', packet_raw[10:12])
        (src_addr, dest_addr) = unpack('!4s4s', packet_raw[12:20])

        self.ip_ihl = self.ip_ihl_ver & 0x0f
        self.ip_ver = (self.ip_ihl_ver & 0xf0) >> 4
        self.ip_tos = (self.ip_tos_ecn & 0xfc) >> 2
        self.ip_ecn = self.ip_tos_ecn & 0x03
        self.ip_flag_df = (self.ip_flag_frag & 0x40) >> 14
        self.ip_flag_mf = (self.ip_flag_frag & 0x20) >> 13
        self.ip_frag_off = self.ip_flag_frag & 0x1f

        self.ip_saddr = socket.inet_ntoa(src_addr)
        self.ip_daddr = socket.inet_ntoa(dest_addr)
        self.data = packet_raw[self.ip_ihl*4:self.ip_tot_len]

        pesudo_ip_header = packet_raw[0:10] + pack('H', 0) + packet_raw[12:20]
        new_chksum = network_chksum(pesudo_ip_header)
        if self.ip_check != new_chksum:
            raise ValueError


class IpSocket(object):
    def __init__(self, src_addr='', dest_addr=''):
        self.sock = DataLinkSocket()
        self.src_addr = src_addr
        self.dest_addr = dest_addr

    def send(self, src_addr, dest_addr, data):
        self.src_addr = src_addr
        self.dest_addr = dest_addr
        ip_packet_for_send = IpPacket(self.src_addr, self.dest_addr, data)
        try:
            self.sock.send(ip_packet_for_send.wrap())
        except Exception as e:
            raise

    def recv(self, packet_type=socket.IPPROTO_TCP):
        while True:
            ip_packet_received = IpPacket()
            packet_raw = self.sock.receive()
            # packet_raw = self.s_recv.recvfrom(self.buffer)
            try:
                ip_packet_received.unwrap(packet_raw)
            except:
                continue
            if ip_packet_received.ip_proto == packet_type and \
               ip_packet_received.ip_saddr == self.dest_addr and \
               ip_packet_received.ip_daddr == self.src_addr:
                return ip_packet_received.data
