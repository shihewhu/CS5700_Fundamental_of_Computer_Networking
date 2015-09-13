#!/usr/bin/python
import socket
import sys
import ssl

if len(sys.argv) == 6:
    nuid = sys.argv[5]
    hostname = sys.argv[4]
    port = 27994
    ssl_flag = True
elif len(sys.argv) == 5:
    nuid = sys.argv[4]
    hostname = sys.argv[3]
    port = int(sys.argv[2])
    ssl_flag = False
elif len(sys.argv) == 4:
    nuid = sys.argv[3]
    hostname = sys.argv[2]
    port = 27994
    ssl_flag = True
elif len(sys.argv) == 3:
    nuid = sys.argv[2]
    hostname = sys.argv[1]
    port = 27993
    ssl_flag = False

def get_solution(msg_recv):
    recv = msg_recv.split(' ')
    data1 = int(recv[2])
    operator = recv[3]
    data2 = int(recv[4])
    if (operator == '+'):
        return data1 + data2
    elif (operator == '-'):
        return data1 - data2
    elif (operator == '*'):
        return data1 * data2
    elif (operator == '/'):
        return data1 / data2
    
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
hellomsg = 'cs5700spring2015 HELLO 001739002\n'

def normal_socket():
    try:
        s.connect((hostname, port))
        s.send(hellomsg)
        msg_recv = s.recv(256)
        while (msg_recv[len(msg_recv) - 4: len(msg_recv) - 1] != 'BYE'):
            solution = get_solution(msg_recv)
            solution_msg = "cs5700spring2015 " + str(solution) + "\n"
            s.send(solution_msg)
            msg_recv = s.recv(256)
        return msg_recv
    finally:
        print "connect is not established"
        s.close()

def ssl_socket():
    simple_ssl = ssl.wrap_socket(s, cert_reqs = ssl.CERT_NONE)
    simple_ssl.connect((hostname,port))
    simple_ssl.write(hellomsg)
    msg_recv = simple_ssl.read()
    while (msg_recv[len(msg_recv) - 4: len(msg_recv) - 1] != 'BYE'):
        solution = get_solution(msg_recv)
        solution_msg = "cs5700spring2015 " + str(solution) + "\n"
        simple_ssl.write(solution_msg)        
        msg_recv = simple_ssl.recv(256)      
    return msg_recv

if ssl_flag:
    print ssl_socket()
else:
    print normal_socket()
