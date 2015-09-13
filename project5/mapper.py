import httplib
import urllib
import threading
import time
import commands
import random
lock = threading.Lock()
rtts = {}


class Mapper():
    """
    This class is used to define a mapper object, which is the main thread
    """
    def __init__(self, client_ip, port, replica_list):
        self.replica_list = replica_list
        self.client_ip = client_ip
        self.port = port
        self.threads = []
        self.pinging = []


    def random_replica(self, client_ip):
        """
        Simple method to get the replica ip_address via the gps distance
        :return:
        """
        # best_loc = self.cal.get_shortest_dist_replica(client_ip)
        # # print best_loc
        # if best_loc == '':
        #     return self.random()
        # else:
        #     return best_loc
        return self.random()


    def random(self):
        return self.replica_list[random.choice(self.replica_list.keys())]


    def _fork_thread(self):
        """
        fork thread according to the number of the replica number
        :return: None
        """
        for key in self.replica_list:
            # print "thread forking"
            thread = SelectThread(self.client_ip, self.port, self.replica_list[key])
            thread.daemon = True
            self.threads.append(thread)

    def _threads_start(self):
        """
        starts all the threads
        :return: None
        """
        for thread in self.threads:
            # print "thread starting"
            thread.start()

    def get_best_replica_ip(self):
        """
        check whether all the thread has finished
        :return: Ip address of the server with the smallest rtt
        """
        self._fork_thread()
        self._threads_start()
        start_time = time.time()
        # if some threads crash or the delay is larger than 10s, return
        # the best ip that has already in the rtts list
        while time.time() - start_time < 8:
            lock.acquire()
            if len(rtts.keys()) == len(self.replica_list.keys()):
                lock.release()
                # print "probe is finished"
                # print "collect the thread"
                for thread in self.threads:
                    thread.join()
                self.threads = []
                break
            else:
                # print "probe is not finished"
                lock.release()
            time.sleep(2)
            # print time.time()
        try:
            print rtts
            return_rtt = {}
            for key in rtts.keys():
                # print key
                if key.split(':')[1] == self.client_ip:
                    return_rtt[float(key.split(':')[0])] = rtts[key]
            # print "result", result
            if sorted(return_rtt.keys())[0] == '' or sorted(return_rtt.keys())[0] == 100000000:
                return -1
            result = return_rtt[sorted(return_rtt.keys())[0]]
        except:
            # print "nothing get"
            return ''

        rtts.clear()
        return result


class SelectThread(threading.Thread):
    """
    This is the thread class used to implement the run method
    """
    def __init__(self, client_ip, port, replica_address):
        threading.Thread.__init__(self)
        self.client_ip = client_ip
        self.replica_address = replica_address
        self.port = port
    # override
    def run(self):
        """
        method implementation
        :return:
        """
        # print "ping"
        selector = Selector(self.client_ip, self.port ,self.replica_address)
        key = selector.call_server_ping(time.time())
        with lock:
            # print [key, self.client_ip]
            rtts[key+":"+self.client_ip] = self.replica_address




class Selector:
    """
    This class is used to define a selector object, which sends all client ip addresses
    to all the replica server and wait for their return
    here we can use subthread to map the ip address
    """
    def __init__(self, client_ip, port, replica_address):
        self.client_ip = client_ip
        self.replica_address = replica_address
        self.port = port

    def call_server_ping(self, start):
        """
         This method is used to call the server start pinging
        :return: the rtt the server returns
        """
        # print "call", self.replica_address,"to ping"
        try:
            conn = httplib.HTTPConnection(self.replica_address, self.port)
            params = urllib.urlencode({"client_ip" : self.client_ip})
            path = "/ping?"+params
            conn.request("GET", path)
            rtt = conn.getresponse().read()
        except:
            rtt = '100000000'
        # print rtt
        finally:
            return rtt