import SocketServer
import re
from mapper import *
from DNSPacket import *
from dns_cache import *

'''
EC2 INFO:
ec2-52-4-98-110.compute-1.amazonaws.com Origin server (running Web server on port 8080)
ec2-52-0-73-113.compute-1.amazonaws.com         N. Virginia
ec2-52-16-219-28.eu-west-1.compute.amazonaws.com        Ireland
ec2-52-11-8-29.us-west-2.compute.amazonaws.com  Oregon, USA
ec2-52-8-12-101.us-west-1.compute.amazonaws.com N. California, USA
ec2-52-28-48-84.eu-central-1.compute.amazonaws.com      Frankfurt, Germany
ec2-52-68-12-77.ap-northeast-1.compute.amazonaws.com    Tokyo, Japan
ec2-52-74-143-5.ap-southeast-1.compute.amazonaws.com    Singapore
ec2-52-64-63-125.ap-southeast-2.compute.amazonaws.com   Sydney, Australia
ec2-54-94-214-108.sa-east-1.compute.amazonaws.com       Sao Paulo, Brazil
'''

IPDictionary = {
    'ec2-52-0-73-113.compute-1.amazonaws.com': '52.0.73.113',
    'ec2-52-16-219-28.eu-west-1.compute.amazonaws.com': '52.16.219.28',
    'ec2-52-11-8-29.us-west-2.compute.amazonaws.com': '52.11.8.29',
    'ec2-52-8-12-101.us-west-1.compute.amazonaws.com': '52.8.12.101',
    'ec2-52-28-48-84.eu-central-1.compute.amazonaws.com': '52.28.48.84',
    'ec2-52-68-12-77.ap-northeast-1.compute.amazonaws.com': '52.68.12.77',
    'ec2-52-74-143-5.ap-southeast-1.compute.amazonaws.com': '52.74.143.5',
    'ec2-52-64-63-125.ap-southeast-2.compute.amazonaws.com': '52.64.63.125',
    'ec2-54-94-214-108.sa-east-1.compute.amazonaws.com': '54.94.214.108'}

DEFAULT = '52.4.98.110'

# the MyDNSRquestHandler is how to deal with the dns request from the client by
# override the handle method in the BaseRequestHandler class
class MyDNSRequestHandler(SocketServer.BaseRequestHandler):
    # override
    def handle(self):
        # print self.client_address
        # get the data from the client
        # print self.request
        data = self.request[0]
        # get the socket, in order the send the response back
        socket = self.request[1]
        # initiate a DNS packet for receiving the data from the client
        packet = DNSPacket()
        packet.disassemble(data)
        # print "ID",packet.ID
        # if the client send the request to host, and the host is the one it want
        # just return the
        # print packet.Question.QNAME
        if packet.Question.QTYPE == 1 and packet.Question.QNAME == DNSServer.authority:
            client_ip = self.client_address[0]
            map = Mapper(client_ip, DNSServer.port, IPDictionary)
            result = DNSServer.cache.search(client_ip)
            if result == -1:
                # print 'start mapping'
                DNSServer.cache.update(client_ip, '')
                result_location = map.random()
                best_replica_address = result_location
                # print best_replica_address
                data = packet.assemble_answer(best_replica_address)
                # print packet.ID
                socket.sendto(data, self.client_address)
                result_active = map.get_best_replica_ip()
                # print "result_active", result_active
                if result_active != '' and result_active != -1:
                    DNSServer.cache.update(client_ip, result_active)
                else:
                    DNSServer.cache.delete(client_ip)
                print DNSServer.cache.cache
            elif result == '':
                # print "ping has been started"
                result_location = map.random()
                best_replica_address = result_location
                data = packet.assemble_answer(best_replica_address)
                socket.sendto(data, self.client_address)
            else:
                best_replica_address = result
                data = packet.assemble_answer(best_replica_address)
                socket.sendto(data, self.client_address)
        else:
            pass

    # def _map(self, client_ip, port, replica_list):
    #     """
    #     Private method to get the best replica ip address
    #     process:
    #     1.Check cache. If the client ip is in the cache, return the according replica address
    #     2.If the client ip address is not cached. Return the location nearest replica address
    #     3.At the same time. start the active measurement and cache the result
    #     :return: the replica ip address
    #     """
    #     result = DNSServer.cache.search(client_ip)
    #     if result == -1:
    #         # print 'start mapping'
    #         map = Mapper(client_ip, port, replica_list)
    #         result_location = map.random()
    #         result_active = map.get_best_replica_ip()
    #         if result_active != '':
    #             DNSServer.cache.update(client_ip, result_active)
    #         return result_location
    #     else:
    #         return result
    #         # return map.random()


# the request should be sent by UDP format, so implements an UDPServer is enough
# We should implement a multithread server

class ThreadedDNSServer(SocketServer.ThreadingMixIn, SocketServer.UDPServer):
    """
    The class used to define the threaded DNS server
    """
    pass


class DNSServer():
    port = 0
    cache = Cache(2*1024*1024)  # public variables cache
    authority = ''
    def __init__(self, port, hostName):
        self.hostname = hostName
        self.port = port

    def _get_ip(self):
        ifconfig = commands.getoutput("ifconfig -a")
        iplist = re.findall(r'inet addr:(.*?) ', ifconfig)
        for ip in iplist:
            if ip != '127.0.0.1':
                return ip

    # run the dns server and start listening to the dns request from the client
    def run(self):
        DNSServer.cache.loads_disk_json()
        ip = self._get_ip()
        # ip = "localhost"
        serverAddress = (ip, self.port)
        DNSServer.port = self.port
        server = ThreadedDNSServer(serverAddress, MyDNSRequestHandler)
        DNSServer.authority = self.hostname
        # server = SocketServer.UDPServer(serverAddress, MyDNSRequestHandler)
        dumps_loads = threaded_dumps_loads()
        dumps_loads.daemon = True
        dumps_loads.start()
        try:
            # while 1:
            # server.handle_request()
            server.serve_forever()
        except KeyboardInterrupt:
            dumps_loads.kill_received = True
            dumps_loads.join()
        server.server_close()
        DNSServer.cache.clear()
        # server_thread = threading.Thread(target=server.serve_forever)
        # server_thread.daemon = True
        # server_thread.start()


class threaded_dumps_loads(threading.Thread):
    """
    A demean thread to loads and dumps the cache.json
    """
    def __init__(self):
        threading.Thread.__init__(self)
        self.kill_received = False
    def run(self):
        start_time = time.time()
        while True:
            if time.time() - start_time >= 5 and not self.kill_received:
                # print "dumps and loads"
                DNSServer.cache.dumps_disk_json()
                DNSServer.cache.loads_disk_json()
                start_time = time.time()
            elif self.kill_received:
                break







