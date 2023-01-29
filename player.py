# Author: Saaketh
# Date: December 8, 2022
# Description: this is the player class

# importing
import socket
import signal
import sys
import argparse
import selectors
from urllib.parse import urlparse

# Server address.
server = ('', '')
# User name for tagging sent messages.
name = ''
# Inventory of items.
inventory = []
# Directions that are possible.
connections = {"north" : "", "south" : "", "east" : "", "west" : "", "up" : "", "down" : ""}

# Timeout time, host for incoming requests and fixed UDP port and 
timeout = 5
hostDiscovery = 'localhost'
portDiscovery = 1234

# Fixed host address of the discovery service
serverDiscovery = (hostDiscovery, portDiscovery)
# Selector for helping us select incoming data from the server and messages typed in by the user.
sel = selectors.DefaultSelector()
# Socket for sending messages.
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Signal handler for graceful exiting. Let the server know when we're gone.
def signal_handler(sig, frame):
    print('Shutting down, interrupt received')
    message='exit'
    client_socket.sendto(message.encode(),server)
    for item in inventory:
        message = f'drop {item}'
        client_socket.sendto(message.encode(), server)
    sys.exit(0)

# Function to handle commands from the user, checking them over and sending to the server as needed.
def process_command(command):

    global server

    # Parse command.
    words = command.split()

    # Send command to server, if it isn't a local only one.
    if (command != 'inventory'):
        message = f'{command}'
        client_socket.sendto(message.encode(), server)

    # Check if we are dropping something.  Only let server know if it is in our inventory.
    if (words[0] == 'drop'):
        if (len(words) != 2):
            print("Invalid command")
            return
        elif (words[1] not in inventory):
            print(f'You are not holding {words[1]}')
            return

    # Check for particular commands of interest from the user.
    # If we exit, we have to drop everything in our inventory into the room.
    if (command == 'exit'):
        for item in inventory:
            message = f'drop {item}'
            client_socket.sendto(message.encode(), server)
        sys.exit(0)

    # If we look, we will be getting the room description to display.
    elif (command == 'look'):
        response, addr = client_socket.recvfrom(1024)
        print(response.decode())

    # If we inventory, we never really reached out to the room, so we just display what we have.
    elif (command == 'inventory'):
        print("You are holding:")
        if (len(inventory) == 0):
            print('  No items')
        else:
            for item in inventory:
                print(f'  {item}')

    # If we take an item, we let the server know and put it in our inventory, assuming we could take it.
    elif (words[0] == 'take'):
        response, addr = client_socket.recvfrom(1024)
        print(response.decode())
        words = response.decode().split()
        if ((len(words) == 2) and (words[1] == 'taken')):
            inventory.append(words[0])

    # If we drop an item, we remove it from our inventory and give it back to the room.
    elif (words[0] == 'drop'):
        response, addr = client_socket.recvfrom(1024)
        print(response.decode())
        inventory.remove(words[1])

    # The player wants to say something ... print the response.
    elif (words[0] == 'say'):
        response, addr = client_socket.recvfrom(1024)
        print(response.decode())

    # If we're wanting to go in a direction, we check with the room and it will tell us if it's a valid
    # direction.  We can then join the new room as we know we've been dropped already from the other one.
    elif (words[0] in connections):
        response, addr = client_socket.recvfrom(1024)
        if (response.decode().startswith("room://")):
            server_address = urlparse(response.decode())
            host = server_address.hostname
            port = server_address.port
            server = (host, port)
            join_room()
        else:
            print(response.decode())
        
    # Otherwise, it's an invalid command so we report it.
    else:
        response, addr = client_socket.recvfrom(1024)
        print(response.decode())

# Function to handle incoming messages from room.  Also look for disconnect messages to shutdown.
def handle_message_from_server(sock, mask):
    response, addr = client_socket.recvfrom(1024)
    words=response.decode().split(' ')
    print()
    if len(words) == 1 and words[0] == 'disconnect':
        print('Exiting... disconnected from server')
        sys.exit(0)
    else:
        print(response.decode())
        do_prompt()

# Function to handle incoming messages from user.
def handle_keyboard_input(file, mask):
    line=sys.stdin.readline()[:-1]
    process_command(line)
    do_prompt()

# Simple function for setting up a prompt for the user.
def do_prompt(skip_line=False):
    if (skip_line):
        print("")
    print("> ", end='', flush=True)
    
# Function to join a room.
def join_room():
    message = f'join {name}'
    client_socket.settimeout(timeout)
    client_socket.sendto(message.encode(), server)
    try:
        response, addr = client_socket.recvfrom(1024)
    except OSError as msg:
        print('Failed to join the server, shutting down...')
        sys.exit()
    print(response.decode())

# Function to find the corresponding address of the server name in the discovery service
def get_server_address(nameServer):
    global server
    message = f'LOOKUP {nameServer}'
    client_socket.sendto(message.encode(), serverDiscovery)
    try:
        response, addr = client_socket.recvfrom(1024)
        words = response.decode().split()
        # Address of server is found
        if (len(words) == 2 and words[0] == 'OK'):
            server_address = urlparse(words[1])
            host = server_address.hostname
            port = server_address.port
            server = (host, port)
            return server
        # Address of server is not found
        else:
            error_message = response.decode().split(' ', 1)[1]
            print(error_message)
            print("The room server is shutting down...")
            message='exit'
            client_socket.sendto(message.encode(),server)
            for item in inventory:
                message = f'drop {item}'
                client_socket.sendto(message.encode(), server)
            sys.exit()
    except OSError as msg:
        print('Failed to use the discovery service, shutting down...')
        sys.exit()

# Our main function.
def main():

    global name
    global client_socket
    global server

    # Register our signal handler for shutting down.
    signal.signal(signal.SIGINT, signal_handler)

    # Check command line arguments.
    parser = argparse.ArgumentParser()
    parser.add_argument("name", help="name for the player in the game")
    parser.add_argument("nameServer", help="name of the room server")
    args = parser.parse_args()

    # Get the name of player and server, find the address of the server by its name
    name = args.name
    nameServer = args.nameServer
    server = get_server_address(nameServer)

    # Send message to enter the room.
    join_room()

    # Prompt the user before beginning.
    do_prompt()

    # Set up our selector.
    sel.register(client_socket, selectors.EVENT_READ, handle_message_from_server)
    sel.register(sys.stdin, selectors.EVENT_READ, handle_keyboard_input)

    # Now do the selection.
    while(True):
        events = sel.select()
        for key, mask in events:
            callback = key.data
            callback(key.fileobj, mask)    

if __name__ == '__main__':
    main()
