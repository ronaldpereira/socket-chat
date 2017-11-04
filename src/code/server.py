import sys
import socket
import select

SERVERID = 65535 # ID do servidor = 65535
BUFSIZE = 400 # Maximum buffer size

# OBSERVATION ABOUT SOCKET.FILENO():
# The socket.fileno() function returns a integer that means the file descriptor, starting from 4.
# That happens because UNIX reserves the first three descriptors to sys.stdin, sys.stdout and the actual socket.
# So, for clients to have the IDs starting from 1, this code always does the conversion of socket.fileno() + 3 for receiving IDs from clients and socket.fileno() - 3 for sending IDs for clients.
# Client side : IDs starts from 1 / Server side : IDs starts from 4

class MessageTypes: # Dictionary to store the message types
	def getMessageType(type): # Method to return the 2 bytes for the message type given
		messageTypes = {
						'OK': (1).to_bytes(2, byteorder='big'),
						'ERRO': (2).to_bytes(2, byteorder='big'),
						'OI': (3).to_bytes(2, byteorder='big'),
						'FLW': (4).to_bytes(2, byteorder='big'),
						'MSG': (5).to_bytes(2, byteorder='big'),
						'CREQ': (6).to_bytes(2, byteorder='big'),
						'CLIST': (7).to_bytes(2, byteorder='big'),
						'OIAP': (13).to_bytes(2, byteorder='big'),
						'MSGAP': (15).to_bytes(2, byteorder='big'),
						'CREQAP': (16).to_bytes(2, byteorder='big'),
						'CLISTAP': (17).to_bytes(2, byteorder='big')
						}

		return messageTypes[type]


class Communication: # Contains all the communication methods
	def headerConstructor(type, destiny, seqnum): # Contruct the header of all message types, except MSGAP
		return MessageTypes.getMessageType(type) + SERVERID.to_bytes(2, byteorder='big') + destiny.to_bytes(2, byteorder='big') + seqnum.to_bytes(2, byteorder='big')

	def sendOK(origin): # Method to send OK to the origin socket
		message = Communication.headerConstructor('OK', origin.fileno()-3, 0)
		origin.send(message)

	def sendERRO(origin): # Method to send ERRO to the origin socket
		message = Communication.headerConstructor('ERRO', origin.fileno()-3, 0)
		origin.send(message)

	def sendCLIST(origin, hostList): # Method to send the ClientLIST (just the IDs) to the origin socket
		message = Communication.headerConstructor('CLIST', origin.fileno()-3, 0)

		message += len(hostList[2:]).to_bytes(2, byteorder='big')

		for sock in hostList[2:]: # Get each socket in the hostList and concatenate it to the message
			message += (sock.fileno()-3).to_bytes(2, byteorder='big')

		origin.send(message)

		recvMessage = origin.recv(BUFSIZE) # Wait for the OK confirmation

		if recvMessage[0:2] == MessageTypes.getMessageType('OK'):
			return

		elif recvMessage[0:2] == MessageTypes.getMessageType('ERRO'):
			print('ERROR!')

	def sendMSG(origin, message, hostList): # Method to send the message from the origin client to the destiny client
		source = int.from_bytes(message[2:4], byteorder='big') + 3
		destiny = int.from_bytes(message[4:6], byteorder='big') + 3

		if source == destiny: # If the source of the message is the same of the destiny, it returns an error message
			Communication.sendERRO(origin)
			return

		if destiny > 3: # If the destiny is greater than 3 (fileno() = 0), it is a unicast
			for host in hostList: # For each host in the hostList
				if host.fileno() == destiny: # If the fileno() of the actual host is the same as the destiny, he is the socket to send the message to
					# host.settimeout(5.0)
				    # try:
				    # 	recvMessage = host.recv(BUFSIZE)
					#
				    # except socket.timeout:
				    # 	print('timeout')
				    #   	Communication.sendERRO(origin)
				    #   	host.close()
				    #   	continue
					host.send(message)
					recvMessage = host.recv(BUFSIZE)

					if recvMessage[0:2] == MessageTypes.getMessageType('OK'):
						Communication.sendOK(origin)

					elif recvMessage[0:2] == MessageTypes.getMessageType('ERRO'):
						Communication.sendERRO(origin)
					return

			Communication.sendERRO(origin) # If none socket is equal to the destiny, returns and error message

		elif destiny == 3: # If the destiny is 3, it means a broadcast message
			valid = True # Valid variable to send the OK or ERRO message to the client
			for host in hostList: # For each host in the hostList that isn't the origin, send the message
				if host != origin:
					host.send(message)
					recvMessage = host.recv(BUFSIZE)

					if recvMessage[0:2] == MessageTypes.getMessageType('ERRO'): # If any message fails, I'm considering that the broadcast failed and it returns an ERRO message to the origin client
						valid = False

			if valid:
				Communication.sendOK(origin)

			else:
				Communication.sendERRO(origin)

	def sendOKAP(origin, nicknames): # Send the nickname for the client
	# Nicknames structure: list with tuples -> [(sock1.fileno(), sock1Nickname), sock2.fileno(), sock2Nickname, ...]
		for nickname in nicknames: # For each tuple in nicknames list
			if origin.fileno() == nickname[0]: # Compare the fileno() with the origin.fileno(), if it could be found, concatenate the nickname with the message
				message = Communication.headerConstructor('OK', origin.fileno()-3, 0)
				message += nickname[1].encode('ascii')
				origin.send(message)
				return

		Communication.sendERRO(origin) # If the nickname of the client couldn't be found, returns an ERRO message

	def sendCLISTAP(origin, nicknames): # Method to send the ClientLIST who has nicknames in the server
		message = Communication.headerConstructor('CLISTAP', origin.fileno()-3, 0)
		message += len(nicknames).to_bytes(2, byteorder='big')

		for nickname in nicknames: # For each nickname in nicknames, concatenate the ID with the nickname, separating each set with a '-'
			message += '-'.encode('ascii') + str((nickname[0]-3)).encode('ascii') + ' '.encode('ascii') + nickname[1].encode('ascii')

		origin.send(message)

		recvMessage = origin.recv(BUFSIZE)

		if recvMessage[0:2] == MessageTypes.getMessageType('OK'):
			return

		elif recvMessage[0:2] == MessageTypes.getMessageType('ERRO'):
			print('ERROR!')

	def sendMSGAP(origin, message, nicknames, hostList): # Send a MSG type to the destiny client
		source = int.from_bytes(message[2:4], byteorder='big') + 3

		isNickname = True # Flag to distinguish between nickname and text in the received message
		nicknameDestiny = '' # String to store the destiny nickname
		text = '' # String to store the origin text
		destiny = 0 # Integer to store the destiny ID

		for c in message[10:]: # For each character in the received message
			if chr(c) == '-': # If a '-' is detected, the nickname string has finished and the text started
				isNickname = False

			if isNickname: # If the actual character is the nickname
				nicknameDestiny += chr(c)

			elif not isNickname: # if the actual character is the text
				text += chr(c)

		text = text[1:] # Excludes the '-' signal from the beggining of the message

		for nickname in nicknames: # For each nickname tuple in the nicknames list
			if nickname[1] == nicknameDestiny: # If we find the nickname in the nickname list
				destiny = nickname[0] # We save the destiny ID

		if not destiny: # If the destiny stills being equal to 0, then it isn't in the nickname list, so returns an ERRO message to the origin
			Communication.sendERRO(origin)

		else: # If the destiny is different from 0, then it is valid
			if source == destiny: # If the origin ID is the same as the destiny ID, returns an ERRO message to the origin
				Communication.sendERRO(origin)
				return

			# This constructs the message with the MSG type to deliver to the destiny client
			sendMessage = MessageTypes.getMessageType('MSG') + message[2:4] + destiny.to_bytes(2, byteorder='big') + message[6:8] + len(text).to_bytes(2, byteorder='big') + text.encode('ascii')

			for host in hostList: # For each host in the hostList
				if host.fileno() == destiny: # If the host is the destiny host, send the message and wait for the response
					host.send(sendMessage)
					recvMessage = host.recv(BUFSIZE)

					if recvMessage[0:2] == MessageTypes.getMessageType('OK'):
						Communication.sendOK(origin) # If the response from the destiny is OK, we send a OK message to the origin client

					elif recvMessage[0:2] == MessageTypes.getMessageType('ERRO'):
						Communication.sendERRO(origin) # If the response from the destiny is ERRO, we send an ERRO message to the origin client
					return

			Communication.sendERRO(origin) # If the host could not be found in the hostList, we send an ERRO message to the origin client


host = '127.0.0.1' # Host address
port = int(sys.argv[1]) # Port received from the command line argument

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Alocate a socket using TCP protocol and IPv4
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Option to reuse the socket address to stop giving the error: Adress is already being used when running the program multiple times

server.bind((host, port)) # Bind the server to the host and the port given
print("Server started and listening.")

server.listen(255) # Listen to a maximum of 255 paralel connections

hostList = [server, sys.stdin] # Host list for the select function
nicknames = [] # Nicknames list for the program extension

active = True # Flag for the server to continue running

while active:
	inputSockets, outputSockets, error = select.select(hostList, hostList[2:], []) # Get all the ready inputSockets and outputSockets (except the server and sys.stdin)

	for sock in inputSockets: # For each socket ready to be read

		if sock == server: # If the socket is the server, try to accept a new connection
			(clientSocket, address) = server.accept()
			print("Connected on client %d from %s." %(clientSocket.fileno()-3, address))

			hostList.append(clientSocket)

		elif sock == sys.stdin: # If the socket is the sys.stdin, try to receive a command
			if sys.stdin.readline().split('\n')[0].upper() == 'SHUTDOWN':
				active = False
				print('Server closed successfully.')

		else: # If the socket is not the server neither the sys.stdin, the message comes from a client socket
			recvMessage = sock.recv(BUFSIZE)

			if recvMessage[0:2] == MessageTypes.getMessageType('MSG'): # If the received message is a MSG type
				Communication.sendMSG(sock, recvMessage, hostList[2:])

			elif recvMessage[0:2] == MessageTypes.getMessageType('OI'): # If the received message is a OI type
				Communication.sendOK(sock)

			elif recvMessage[0:2] == MessageTypes.getMessageType('FLW'): # If the received message is a FLW type
				Communication.sendOK(sock)
				hostList.remove(sock) # Remove the origin socket from the hostList

				for nickname in nicknames:
					if nickname[0] == sock.fileno(): # If the origin socket registered a nickname, remove it from the nicknames list
						nicknames.remove(nickname)

				sock.close() # Close the connection with the origin socket

			elif recvMessage[0:2] == MessageTypes.getMessageType('CREQ'): # If the received message is a CREQ type
				Communication.sendCLIST(sock, hostList)

			elif recvMessage[0:2] == MessageTypes.getMessageType('OIAP'): # If the received message is a OIAP type
				if recvMessage[8:]:

					for nickname in nicknames:
						if nickname[0] == sock.fileno(): # If the origin socket already has a registered nickname, remove it from the nicknames list
							nicknames.remove(nickname)

					nicknames.append((sock.fileno(), recvMessage[8:].decode())) # And append a new one for him
					# This avoids the same socket ID from having two different nicknames

				Communication.sendOKAP(sock, nicknames)

			elif recvMessage[0:2] == MessageTypes.getMessageType('CREQAP'): # If the received message is a CREAP type
				Communication.sendCLISTAP(sock, nicknames)

			elif recvMessage[0:2] == MessageTypes.getMessageType('MSGAP'): # If the received message is a MSGAP type
				Communication.sendMSGAP(sock, recvMessage, nicknames, hostList[2:])

server.close() # Close the server socket connection