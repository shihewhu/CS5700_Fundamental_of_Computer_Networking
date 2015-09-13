import SocketServer
import BaseHTTPServer
import urllib
import re
import commands
from http_cache import Cache



class Handler(BaseHTTPServer.BaseHTTPRequestHandler):
    """
    docstring for Http
    This class is used for defining the http request handler object.
    There is a static variable: origin used for store the origin host name for query
    do_GET method is used to handle the GET request the client sent
    Handling process contains 2 steps:
    1. query the cache
    2. query the origin
    send the content back to the client
    """

    origin = '' # origin name port
    def do_GET(self):
        """

        :return:
        """
        """Respond to a ping request"""
        # print self.path
        if self._is_ping_request(self.path):
            # print self.headers
            self._do_ping(self.path[6:])
            return
        """Respond to a GET request."""
        content = HttpServer.cache.search(self.path)

        if content == -1: # The content is not in the cache, query the origin to get it.
            # print self.path + " is not in cache"
            response = self._query_origin(self.path)
            code = response.getcode()
            header = response.headers
            content = response.read()
            self.send_response(code)
            self.wfile.write(header)
            # self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(content)
            if code == 200:
                HttpServer.cache.update(self.path, content)
        else:
            # print self.path + " is in cache" # the content is in the cache, return it directly
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(content)

    def _is_ping_request(self, path):
        return "/ping" in path


    def _do_ping(self, path):
        client_address = path.split('=')[1]
        RTT = self._ping(client_address)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(str(RTT))

    def _ping(self, client_address):
        # print client_address
        result = commands.getoutput('/usr/bin/scamper -c \'ping -c 1\' -i ' + client_address)
        # print result
        # print result.split('\n')[1].split()[-2]
        RTT = result.split('\n')[1].split()[-2].split('=')[-1]
        if RTT == 'statistics':
            RTT = ''
        # print RTT
        return RTT


    def _query_origin(self, path):
        """
        query the client request to the origin
        :param path: the path of the client gives
        :return: the request object the origin returns
        """
        # print "http://"+Handler.origin+path
        if len(Handler.origin.split(':')) == 1:
            Handler.origin += ':8080'
        request = urllib.urlopen("http://"+Handler.origin + path)
        # print request.geturl()
        return request



# class ThreadedHttpServer(SocketServer.ThreadingMixIn, BaseHTTPServer.HTTPServer):
#     pass


class HttpServer():
    """
    This class is used to define a HttpServer object, the origin and port is privoded by the user
    run method will create HTTPServer and make it start serving
    If the server receives a keyboard interrupt, it will end serving and close
    """
    cache = Cache()
    def __init__(self, origin, port):
        self.port = port
        self.origin = origin

    def get_ip(self):
        """
        get the ip of the local machine
        :return: the ip of the local machine
        """
        ifconfig = commands.getoutput("ifconfig -a")
        iplist = re.findall(r'inet addr:(.*?) ', ifconfig)
        # print iplist
        for ip in iplist:
            if ip != '127.0.0.1':
                return ip

    def run(self):
        """
        run the server
        :return:
        """
        HttpServer.cache.new_dir()
        HttpServer.cache.load_from_disk()
        # server_class = BaseHTTPServer.HTTPServer
        Handler.origin = self.origin
        ip = self.get_ip()
        # print ip
        # ip = "localhost" # used for local test
        # httpd = ThreadedHttpServer((ip, self.port), Handler)
        httpd = BaseHTTPServer.HTTPServer((ip, self.port), Handler)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
        httpd.server_close()


