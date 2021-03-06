If you are not root please run the program

    sudo ./rawhttpget <url>


## HighLevel Approach
We design the whole program layer by layer(OSI layer). Each layer provides api for the higher layer and 
uses the api provided by the lower layer. Each layer has a class called [packetname]Socket(i.e TcpSocket).
each class maintain a socket provided by the lower layer(like in TcpSocket class has a IpSocket). In datalink
layer, the Socket is RAW_SOCK provided by OS.
When sending data, each layer will wrap its own packet and call the send api provided by lower layer and put
its own packet as parameter of the api(sending it to the lower layer). Each layer see the packet delievered from the higher layer as data. In datalink layer, the program will use RAW socket to send the packet
When receiving data, each layer will unwrap the packet it received and valid the checksum and MAC address, ip address or port and return them to the higher layer. The application will grep the data, remove the header, and dealing with the chunk(if the data is chunked) and save it to a file in the local folder.
## Challenges
* The transport layer is rather complicated, we refer the high level socket(SOCK_STREAM) and implement the same api 
such as connect, send, recv_all and close. The connect method is used to execute the three-way handshake. The send method u
ses the send method in network layer to send the data. The recv_all method
* When we do the checksum validation, we found the checksum is always wrong. Then we found that the header
of the tcp packet sent by the server contains option, and the length is larger than 20. We use ihl * 4 to do the checksum, then correct!
* We noticesd that the data is chunked when the server sending, so we removed every chunk length from the data by regular expression
* When we receive a packet, we unwrap it. However, at first, we return the whole packet to the higher layer, We noticed this problem and just return the data
* in the network layer, when we got a ip packet, at first, we get the data just by remove the header. However, the padding will cause the checksum validataion error, then we used the total length to get the data
* The challenging part of extra in datalink layer is how to find the gateway ip using ARP. We designed a method called get_mac_addr_by_arp() to solve the problem. In the method, We try to simulate the process of ARP. In order to get the mac 
address of the server, We assemble a ARP packet as the data of the frame and send the frame out as a broadcast ffff.ffff.ffff. 
Then tell the whole LAN in server, and asking who has the given ip address. If the machine knows that it has the ip, then it will send the packet 
with the MAC address that replied. Now, we got the mac address of the server. We can assemble the ethernet header and then
connect with the server and send the assembled packet out to the server. Next, We have to deal with some small problems, 
using commands to the get the ip and mac address of the local machine. 

## Team Member Responsibilities

###  He Shi
My work focuses on the transport layer and network layer.
I referred the logic of high level socket and tried to simulate all the process of the high level socket
* To the network layer, I defined the ip socket class to provide api for the transport layer. 
* To the transport layer, I defined the tcp socket class to provide api for the application layer.
* I implemented three-way handshake, time out, retransmission, out-order tcp packet dealing and congestion control
(although in this program, it seems that it is not useful) in the transport layer.
* dealing the chunked data

### Shifu Xu
My work focus on the upper layer and lower layer, which are application (http) layer and datalink(ethernet) layer.
* For the http layer, I defined an assemble_http_header() function for assembling the HTTP GET header. Next, I defined
the send() and receive() using the socket initiated from transport layer, send and recv_all() method provided by transport
layer. Sometimes, the data we received may have chunk number at the frist line, then we have to deal with the chunk in the
program. Firstly, I check whether the downloaded file contains the chunk number, it does not, then return right now; if 
it does not, I get the chunk from the file, and read the number of bytes from the data according to the chunk. In the 
end, if I recevied the 0 as the chunk, it means that I have received all the data from the server. Next part is how to 
store the data in the folder according the requirements. I defined a save_file() method to deal with If the url ends with 
the a file name like 'project4.php', 'name.html', 'result.asp' and so on, I get the file name and write the data into the
file whose name is the file name in the url. However, when the url ends with the '/', then I just use the default name 
'index.html' as the file name.
* For the bonus part which is datalink layer. I used the AF_PACKET raw socket instead of IPPROTO_RAW. In this layer, I 
have to deal with frame for each packet from the upper layer. The challenging part is to do MAC resolution with ARP 
requests. I designed three classes, one is called EtherPacket, one is called ARPPacket, the last one is called 
DataLinkSocket. EtherPacket provides assemble() method for assembling the frame, disassemble() method for disassembling
the received packet. ARPPacket is different with normal frame, and the ARPPacket class provides the function like 
assemble() for assemebling the certain ARP packet and disassemble() for disassembling the received ARP packets.
