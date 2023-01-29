# Client-Server-Game-Application

The discovery service you create will map room names into server addresses of the form room://host:port.
Before starting any room servers or player clients, your discovery service would be started.  It will listen on a fixed UDP port for incoming requests.  This port number will be stored as a constant in the discovery service, as well as the player client and room service.  The player client and room service will also have the host address for the discovery service stored in a constant.  (Ordinarily, we would use broadcasting to find the discovery service, but the university would likely not like all of us broadcasting around quite so much ...)
The discovery server must support the following messages:
REGISTER room://host:port name
Registers a server, with host giving the name of your server, port giving its port number, and name being the name of the room, given as a parameter to the room server on the command line.
DEREGISTER name
Deletes the registration for the server registered under the given name.
LOOKUP name
Attempts to lookup the address of a server with the given name.
In response to messages, the discovery service will return the following responses:
OK result
The request was successful; result contains the optional results of the request.  (Nothing for REGISTER/DEREGISTER, the address for the server with LOOKUP.)
NOTOK msg
The request was not successful; msg contains an error message describing the result.
When a room server starts, it no longer takes a port number as a command line parameter.  Instead, the server will ask the system to allocate it an available port number.  The server will then register with the discovery service by sending it a REGISTER request.  When receiving a REGISTER request, the discovery service will record the name to address mapping for the incoming server if they are unique, sending an OK response back to the server.  If the name or the address have been previously registered, the discovery service will send a NOTOK response with an appropriate error message.  In such a case, the room server reports the error to the user and terminates.
When a room server terminates, it sends the discovery service a DEREGISTER request.  When receiving a DEREGISTER request, the discovery service will attempt to remove the registration for the named server from its records.  If the record existed and was removed, it sends an OK response back to the server.  Otherwise, it sends a NOTOK response back to the server.  (In practice, this shouldn't happen, but should things should handle errors appropriately.)
Connections to other rooms are still specified on the command line when starting a room server using the -n, -s, -e, -w, -u, and -d parameters.  This time, however, instead of specifying these connections using the addresses of the corresponding servers, you would simply use the name of the server instead.  For example, if a room is connected to the Foyer to its north, you would indicate this by passing the parameters "-n Foyer" to the server on startup, instead of specifying the address of the other server.
When a player client starts, it no longer takes a server address as a parameter on its command line.  Instead, it takes the name of room to start in.  For example, if player Alice wants to start in the Foyer, they would invoke their client by executing:  "python3 player.py Alice Foyer"
In the process of joining a room, the player client first determines the address of the server hosting the room by issuing a LOOKUP request to the discovery service.  On receiving a LOOKUP request, the discovery service will attempt to find the named server in its records.  On success, it returns an OK response to the requesting client, sending along the address of the server in room://host:port format to the client.  If the named room does not exist in its records, the discovery service instead returns a NOTOK response along with an error message.  In such a case, the receiving client would print the error message to the user and terminate.
Similarly, whenever the player moves from room to room, these new joins will follow a similar process, with a LOOKUP request to the discovery service providing the address of the new room service.
If a room server needs to connect to another server, for example to transfer inventories of moving players if the inventories were stored server-side instead of client-side, the server will similarly use a LOOKUP request to the discovery service to get the address it needs to send it its message.
