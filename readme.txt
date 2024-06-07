QVTP - QUIC Video Transfer Protocol

Team Members:
Sidhant Gumber: 14664480
Nakul Narang: 14649250
Shantanu Sharma: 14671956
 
Overview

QVTP (QUIC Video Transfer Protocol) is a file transfer protocol implemented over QUIC to enable the reliable transfer of video files. The protocol ensures data integrity and handles stateful connections using session tickets. Our current implementation handles client side uploads correctly by encoding the video in byte sized chunks each being 10kb (our testing video was 330kb so we chose a lower value to ensure that serialization into packets is done correctly). However the server only receives a few data packets before being stuck and we get error messages that we tried our best to resolve but unfortunately, this was the most we could do. This indicates that the client-side code successfully serializes the video data, but the server encounters issues with deserializing the received data. The errors suggest problems with character encoding, indicating that the data might not be correctly interpreted as binary.

1. Introduction:
    -This document outlines the design and implementation details of our custom network protocol.

2. Protocol Overview:
    -Our protocol is designed to provide reliable communication between clients and servers over a network.
    It ensures stateful communication through the implementation of a Deterministic Finite Automaton (DFA).
    The protocol supports various services such as video data transfer(upload/download), request-response interactions, and error handling.

3. Features:
    -Statefulness: Protocol state management is ensured via the class SessionTicketStore in quic_engine.py. 
    -Service Binding: The server binds to a hardcoded port number: 4433 (but cal also be changed using command line arguments)
    -Client Configuration: Clients can specify the hostname or IP address of the server using command line arguments. Defaults are local host and port number: 4433
    -Server Configuration: Similar to clients, servers can receive configuration information from command line parameters.


4. Server Deployment:
Deploy the server by specifying configuration parameters such as port number, logging settings, and other required details through a configuration file or command line parameters.
Default server side command line argument: 

python qvtp.py server 

AFTER RUNNING THE SERVER OPEN A NEW TERMINNAL WINDOW AND RUN THE CLIENT BY PASSING IN THE PATH OF THE VIDEO FILE
Client Deployment:
To deploy the client, specify the server's hostname or IP address either through a configuration file or command line arguments. Ensure the correct port number is provided for communication.
Default client side command line argument:

python qvtp.py client -v testvideo.mp4

After successfully converting into bytes the uploaded video can be viewed in the same directory as received_testvideo.mp4. It will be invalid because we couldn't deserialize it properly but this is what the structure of the implementation is. We would greatly appreciate the opportunity to sit down with you(after this has been graded) to figure out where our code went wrong. 


5.) Conclusion:
    Our protocol design emphasizes stateful communication, service flexibility, and ease of deployment. But given the encoding and deserialization issue we weren't able to fully implement it. The code demonstrates the basic functionality of a client-server video transfer system using QUIC. However, there are areas where the implementation could be strengthened to improve reliability, error handling, and data integrity.

NOTE: We uploaded the project on github for ease of submission after finishing development so individual contributions won't be visible.