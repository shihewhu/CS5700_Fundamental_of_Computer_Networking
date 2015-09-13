from transport import TcpSocket, TcpPacket
from urlparse import urlparse
from time import time
from cStringIO import StringIO
import re
TIME_OUT = 60 # one min default

class Http:
    def __init__(self):
        # define sock by the method provided by transport layer
        self.sock = TcpSocket()
        self.chunked = False
        self.content = ''
        self.header = ''

    def assemble_http_header(self, path, host):
        # assemble the http header in the application layer
        http_header = ''
        http_header += 'GET ' + path + ' HTTP/1.1\n'
        http_header += 'Host: ' + host + '\r\n'
        http_header += 'Connection: keep-alive\r\n'
        http_header += 'Accept: text/html\r\n'
        http_header += '\r\n'

        # make sure the http header is even
        if len(http_header) % 2 != 0:
            http_header += ' '
        
        return http_header

    def send(self, data):
        # call the send method provided by transort layer
        self.sock.send(data)

    def receive(self):
        data_recv = ''
        content_len = 0
        flag_received = False
        time_started = time()

        # call the method recv_all provided by transport layer
        data_recv = self.sock.recv_all()
        #remove the http header
        page = self.remove_header(data_recv)
        # tell whether the data received is chunked, if chunked, remove the chunk length 
        if self.parse_chunked(page):
            try:
                self.content = self.remove_chunk_length(page)
            except ValueError:
                self.content = page
        else:
            self.content = page
        
        return self.content
        
    def remove_header(self, data):
        # function for removing the http header
        header_offset = data.split('\r\n\r\n', 1)
        self.header = header_offset[0]
        return header_offset[1]

    def parse_chunked(self, data):
        # determine whether chuck is appeared in the downloaded file
        # get the chunk from the first line of downloaded file and try to match that
        first_line = data.split('\r\n', 1)[0]
        m = re.match(r'^[a-zA-Z0-9]+$', first_line)

        # if it exists, return true, else, return false
        if m is not None:
            return True
        if m is None:
            return False

    def remove_chunk_length(self, data):
        content = []
        while True:
            # get the chunk number and rest data respectively
            first_line = data.split('\r\n', 1)[0]
            rest_data = data.split('\r\n', 1)[1]
            m = re.match(r'^[a-zA-Z0-9]+$', first_line)
            # find chunk, and read data according to the chunk
            if m is not None:
                chunk_size = int(m.group(0), 16)
                content.append(rest_data[:chunk_size])
                data = rest_data[chunk_size + 2:]
                # if chuck is 0, exit out of the while loop, means we have received all the data
                if chunk_size == 0:
                    break
            # if can not find chunk, raise exception
            elif m is None:
                raise ValueError

        return ''.join(content)

    def save_file(self, data, url):
        # save file into the local folder
        new_file_name = ''

        # deal with the default name of downloaded page
        path = urlparse(url).path
        file_name = path.split('/')[-1]
        if file_name == '':
            new_file_name = "index.html"
        else:
            new_file_name = file_name

        # write the data into the fixed file and close the stream
        f = open(new_file_name, 'wb')
        f.write(data)
        f.close()

    def grep_data(self, url):
        # check the format of the url, keep the http://
        if 'http://' == url[:7]:
            pass
        else:
            url += 'http://'

        # get the host and path through the url_obj
        url_obj = urlparse(url)
        host = url_obj.netloc
        path = url_obj.path
        if path == '':
            path = '/'
        else:
            pass

        # connect the socket to the server, the connect method is provide by transport layer
        port = 80
        self.sock.connect(host, port)

        # assemble the http header
        data_sent = self.assemble_http_header(path, host)

        # send the data
        self.send(data_sent)

        # receive the data from the server
        data_recv = self.receive()

        # print data_recv
        self.save_file(data_recv, url)

        # close the connection using close method provided by tarnsport layer
        self.sock.close()