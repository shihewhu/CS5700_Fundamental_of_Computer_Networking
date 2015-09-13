from struct import *
import socket
import random

# define DNS packet
class DNSPacket:
    def __init__(self):
        self.ID = random.randint(0, 65535)
        self.QR = 0  # query (0); response (1)
        self.Opcode = 0  # representing standard query
        self.AA = 0  # whether or not the the response you receive is authoritative
        self.TC = 0  # exit if you receive a response that is truncated
        self.RD = 0  # set for recursive
        self.RA = 0  # recursive available
        self.Z = 0  # reserved for future use, must be 0
        self.RCODE = 0  # whether or not you are desire for recursion
        self.Flags = self.RCODE + (self.Z << 4) + (self.RA << 7) + (self.RD << 8) + (self.TC << 9) + (self.AA << 10) + (
            self.Opcode << 11) + (self.QR << 15)
        self.QDCOUNT = 0  # number of questions
        self.ANCOUNT = 0  # number of responses
        self.NSCOUNT = 0
        self.ARCOUNT = 0
        self.Question = DNSQuestion()
        self.Answer = DNSAnswer()

    # assemble the DNS question packet
    def assemble_question(self):
        header = pack('>HHHHHH', self.ID, self.Flags, self.QDCOUNT, self.ANCOUNT, self.NSCOUNT, self.ARCOUNT)
        return header + self.Question.assemble()

    # assemble the DNS answer packet
    def assemble_answer(self, ip):
        self.Flags = 0x8180  # meaning it is a response, recursion requested, server can do recursion
        self.ANCOUNT = 1  # there is one answer
        self.ARCOUNT = 0
        self.Answer = DNSAnswer()
        # get the header and the question part of the packet
        temp = self.assemble_question()
        # return the whole packet, and it is a response packet
        return temp + self.Answer.assemble(ip)

    def disassemble(self, dns_packet):
        # disassemble the header of dns packet
        [self.ID, self.Flags, self.QDCOUNT, self.ANCOUNT, self.NSCOUNT, self.ARCOUNT] = unpack(">HHHHHH",
                                                                                               dns_packet[0:12])
        # print self.ID
        # get the question part of dns packet
        self.Question = DNSQuestion()
        self.Question.disassemble(dns_packet[12:])
        # set the answer part of dns packet
        self.Answer = None



class DNSQuestion:
    def __init__(self):
        self.QNAME = ''  # the name of the web address
        self.QTYPE = 0  # type, default is A (1)
        self.QCLASS = 0  # class, default is internet address (1)

    # assemble the question part of the dns packet
    def assemble(self):
        # set the qname of the questin part
        domainNameList = self.QNAME.split('.')
        QNameList = []
        for name in domainNameList:
            QNameList.append(chr(len(name)) + name)
        # get the name attribute of the qeustion part
        QName = ''.join(QNameList) + '\x00'  # \x00 is the endpoint of the name
        # return the whole question part
        return QName + pack('>HH', self.QTYPE, self.QCLASS)

    def disassemble(self, raw_data):
        # print len(raw_data)
        # find the \x00 part in the raw_data
        end = 0
        while ord(raw_data[end]) != 0:
            end += 1
        pointer = 0
        temp = []
        while pointer <= end:
            content = ord(raw_data[pointer])
            # encounter the end of the qname
            if content == 0:
                break
            pointer += 1
            temp.append(raw_data[pointer:pointer + content])
            pointer += content
        # get the domain name from the raw_data
        self.QNAME = '.'.join(temp)
        # disassemble the QTYPE AND QCLASS from the raw_data
        [self.QTYPE, self.QCLASS] = unpack('>HH', raw_data[end + 1:end + 5])


class DNSAnswer:
    def __init__(self):
        self.NAME = 0xc00c  # the default name of the domain name
        self.TYPE = 0x0001  # type, default is A (1)
        self.CLASS = 0x0001  # class, default is internet address (1)
        self.TTL = 100  # the number of seconds that can be cached
        self.RDLENGTH = 4  # the length of ip address is 4 bytes
        self.RDATA = 0  # the ip address

    def assemble(self, ip):
        # return the whole answer part
        # print ip
        return pack('>HHHLH4s', self.NAME, self.TYPE, self.CLASS, self.TTL, self.RDLENGTH, socket.inet_aton(ip))