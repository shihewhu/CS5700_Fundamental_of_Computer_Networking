#Create a simulator object
set ns [new Simulator]

#Read rate of cbr and variant of tcp from the command line
#Check availbility of inputs
if {$argc < 3} {
        puts "the script requires three numbers to be inputed"
        puts "the first parameter represents the rate of the cbr"
        puts "the second parameter represents the variants of tcp"
        puts "the third parameter represents another variants of tcp"
}

if {$argc > 3} {
        puts "the script requires three numbers to be inputed."
        puts "the first parameter represents the rate of the cbr"
        puts "the second parameter represents the variants of tcp"
        puts "the third parameter represents another variants of tcp"
}

#Get system time
set systemTime [clock microseconds]
puts $systemTime

#Change default seed according to the system time
$defaultRNG seed [expr $systemTime % 10000000]

#Open the Trace file
set tf [open out2.tr w]
$ns trace-all $tf

#Define a 'finish' procedure
proc finish {} {
        global ns tf
        $ns flush-trace
        #Close the Trace file
        close $tf
        exit 0
}

#Create six nodes
set n1 [$ns node]
set n2 [$ns node]
set n3 [$ns node]
set n4 [$ns node]
set n5 [$ns node]
set n6 [$ns node]

#Create links between the nodes using DropTail
$ns duplex-link $n1 $n2 10Mb 10ms DropTail
$ns duplex-link $n2 $n5 10Mb 10ms DropTail
$ns duplex-link $n2 $n3 10Mb 10ms DropTail
$ns duplex-link $n3 $n4 10Mb 10ms DropTail
$ns duplex-link $n3 $n6 10Mb 10ms DropTail

# Set topology as follows
$ns duplex-link-op $n1 $n2 orient right-down
$ns duplex-link-op $n5 $n2 orient right-up
$ns duplex-link-op $n2 $n3 orient right
$ns duplex-link-op $n4 $n3 orient left-down
$ns duplex-link-op $n6 $n3 orient left-up

#Set Queue size of link (n2 - n3) to 10
$ns queue-limit $n2 $n3 10

#Create a UDP agent and attach it to node n2
set udp0 [new Agent/UDP]
$udp0 set class_ 1
$ns attach-agent $n2 $udp0

# Create a CBR traffic source and attach it to udp0
set val [lindex $argv 0]
append val Mb
set cbr0 [new Application/Traffic/CBR]
$cbr0 set packetSize_ 1000
$cbr0 set interval_ 0.005
$cbr0 set rate_ $val
$cbr0 set type_ CBR
$cbr0 set random_ 1
$cbr0 attach-agent $udp0

#Create a Null agent (a traffic sink) and attach it to node n3
set null0 [new Agent/Null]
$ns attach-agent $n3 $null0

#Create a TCP agent and attach it to node n1
set type0 Agent/
append type0 [lindex $argv 1]
set tcp0 [new $type0]
$tcp0 set class_ 2
$tcp0 set window_ 150
$ns attach-agent $n1 $tcp0

# Create a FTP and attach it to tcp0
set ftp0 [new Application/FTP]
$ftp0 attach-agent $tcp0
$ftp0 set type_ FTP

#Create a SINK agent (a TCP sink) and attach it to the node n4
set sink0 [new Agent/TCPSink]
$ns attach-agent $n4 $sink0

#Create another TCP agent and attach it to node n5
set type1 Agent/
append type1 [lindex $argv 2]
set tcp1 [new $type1]
$tcp1 set class_ 3
$tcp1 set window_ 150
$ns attach-agent $n5 $tcp1

# Create another FTP and attach it to tcp1
set ftp1 [new Application/FTP]
$ftp1 attach-agent $tcp1
$ftp1 set type_ FTP

#Create a SINK agent (a TCP sink) and attach it to the node n4
set sink1 [new Agent/TCPSink]
$ns attach-agent $n6 $sink1

#Connect the traffic sources with the traffic sink
$ns connect $udp0 $null0
$udp0 set fid_ 1
$ns connect $tcp0 $sink0
$tcp0 set fid_ 2
$ns connect $tcp1 $sink1
$tcp1 set fid_ 3

#Schedule events for the CBR agents
$ns at 0.5 "$cbr0 start"
$ns at 1.0 "$ftp0 start"
$ns at 4.0 "$ftp1 start"
$ns at 16.0 "$ftp0 stop"
$ns at 19.0 "$ftp1 stop"
$ns at 20.0 "$cbr0 stop"
#Call the finish procedure after 5 seconds of simulation time
$ns at 20.1 "finish"

#Run the simulation
$ns run