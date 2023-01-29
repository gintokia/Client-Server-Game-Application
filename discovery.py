# Author: Saaketh
# Date: December 8, 2022
# Description: this is the discovery class

# importing
import socket
import signal
import sys

# Fixed UDP port and host for incoming requests, and fixed host address of the discovery service
portDiscovery = 1234
hostDiscovery = 'localhost'
serverDiscovery = (hostDiscovery, portDiscovery)

# The discovery server's socket.
discovery_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
entryRegistry = {}

# Signal handler for graceful exiting.
def signal_handler(sig, frame):
    print('Shutting down... interrupt received')
    sys.exit(0)

# Process incoming message.
def process_message(message):

    global server

    # Parse words.
    words = message.split()
    
    if (words[0] == 'REGISTER'):
        if (words[1].startswith("room://") and len(words) == 3):
            if (words[2] not in entryRegistry and words[1] not in entryRegistry.values()):
                entryRegistry[words[2]] = words[1]
                return 'OK'
            else:
                error_message = "Address or name have been previously registered"
                return 'NOTOK' + " " + error_message
        else:
            error_message = "Server address invalid for registration"
            return 'NOTOK' + " " + error_message
    
    elif (words[0] == 'LOOKUP'):
        if (words[1] in entryRegistry and len(words) == 2):
            server_address = entryRegistry[words[1]]
            return 'OK' + " " + server_address

        else:
            error_message = "Failed to find server address in registration"
            return 'NOTOK' + " " + error_message
    
    elif (words[0] == 'DEREGISTER'):
        if (words[1] in entryRegistry and len(words) == 2):
            del entryRegistry[words[1]]
            if (words[1] not in entryRegistry):
                return 'OK'
            else:
                error_message = "Failed to deregister the server address"
                return 'NOTOK' + " " + error_message
        else:
            error_message = "Server address invalid for deregistration"
            return 'NOTOK' + " " + error_message

    # Otherwise, the message is invalid.
    else:
        return 'NOTOK' + " " + "Invalid message"
    
def main():

    signal.signal(signal.SIGINT, signal_handler)
    discovery_socket.bind(('', portDiscovery))
    print("Discovery service is working...")
    
    # Loop forever waiting for messages from clients.
    while True:
        # Receive a packet from a client and process it.
        message, addr = discovery_socket.recvfrom(1024)
        # Process the message and retrieve a response.
        response = process_message(message.decode())
        # Send the response message back to the client.
        discovery_socket.sendto(response.encode(), addr)

if __name__ == '__main__':
    main()
    
