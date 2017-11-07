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
	def __init__(self):
		self.clientID = 0 # Saves the client side given ID for each client
		self.seqnum = 0 # Saves the sequence number of the message

	def headerConstructor(self, type, destiny): # Contruct the header of all message types, except MSGAP
		return MessageTypes.getMessageType(type) + self.clientID.to_bytes(2, byteorder='big') + destiny.to_bytes(2, byteorder='big') + self.seqnum.to_bytes(2, byteorder='big')

	def sendOK(self, client): # Method to send OK message to the server
		message = self.headerConstructor('OK', SERVERID)
		client.send(message)

	def sendOI(self, client): # Method to send OI message to the server
		message = self.headerConstructor('OI', SERVERID)
		client.send(message)
		recvMessage = client.recv(BUFSIZE)

		if recvMessage[0:2] == MessageTypes.getMessageType('OK'):
			self.clientID = int.from_bytes(recvMessage[4:6], byteorder='big')
			self.seqnum += 1
			print("Your ID is:", self.clientID)

		elif recvMessage[0:2] == MessageTypes.getMessageType('ERRO'):
			print('ERROR!')

	def sendFLW(self, client): # Method to send FLW message to the server
		message = self.headerConstructor('FLW', SERVERID)
		client.send(message)
		recvMessage = client.recv(BUFSIZE)

		if recvMessage[0:2] == MessageTypes.getMessageType('OK'):
			self.seqnum += 1
			client.close()
			print("Connection closed successfully!")

		elif recvMessage[0:2] == MessageTypes.getMessageType('ERRO'):
			print('ERROR!')

	def sendCREQ(self, client): # Method to send Client REQuirement message to the server
		message = self.headerConstructor('CREQ', SERVERID)
		client.send(message)
		recvMessage = client.recv(BUFSIZE)

		if recvMessage[0:2] == MessageTypes.getMessageType('CLIST'):
			self.seqnum += 1
			numberClients = int.from_bytes(recvMessage[8:10], byteorder='big')
			print("Number of connected clients:",numberClients)

			print('Connected IDs:',end=' ')

			for i in range(1,numberClients+1): # For each client ID received, print it
				print(int.from_bytes(recvMessage[(8+i*2):(10+i*2)], byteorder='big'), end=' ')
			print('')

		message = self.headerConstructor('OK', SERVERID)
		client.send(message)

	def sendMSG(self, client, destiny, text): # Method to send a MSG message to the destiny socket
		message = self.headerConstructor('MSG', destiny)
		message += len(text).to_bytes(2, byteorder='big')

		for c in text: # For each character in the text, convert it to a byte and concatenate it to the message
			message += int(c).to_bytes(1, byteorder='big')

		client.send(message)

		recvMessage = client.recv(BUFSIZE)

		if recvMessage[0:2] == MessageTypes.getMessageType('OK'):
			self.seqnum += 1
			print("Message delivered.")

		elif recvMessage[0:2] == MessageTypes.getMessageType('ERRO'):
			print("ERROR!")

	def sendOIAP(self, client, nickname=''): # Method to send a OIAP message to the server. Note here that the nickname is an empty string by default, unless it is sent by the function caller
		message = self.headerConstructor('OIAP', SERVERID)

		if nickname: # If the nickname exists
			message += nickname # Concatenate the nickname to the message to be sent for the server. Using this, you will set your actual nickname in the server side

		client.send(message)

		recvMessage = client.recv(BUFSIZE)

		if recvMessage[0:2] == MessageTypes.getMessageType('OK'):
			self.seqnum += 1
			print("Your nickname is:", recvMessage[8:].decode()) # Prints the nickname received from the server side

		elif recvMessage[0:2] == MessageTypes.getMessageType('ERRO'):
			print("ERROR!")

	def sendCREQAP(self, client): # Method to send a Client REQuirement AP (nickname) message to the server
		message = self.headerConstructor('CREQAP', SERVERID)
		client.send(message)

		recvMessage = client.recv(BUFSIZE)

		if recvMessage[0:2] == MessageTypes.getMessageType('CLISTAP'):
			self.seqnum += 1
			numberNicknameClients = int.from_bytes(recvMessage[8:10], byteorder='big')
			print("Number of connected clients with nicknames:",numberNicknameClients)

			for c in recvMessage[10:]: # For each character in the text, separated by '-', print the socket ID and the socket nickname
				if chr(c) == '-':
					print('')
				else:
					print(chr(c), end='')
			print('')

		message = self.headerConstructor('OK', SERVERID)
		client.send(message)

	def sendMSGAP(self, client, destinyNickname, text): # Method to send a MSGAP message to the server
		message = MessageTypes.getMessageType('MSGAP') + self.clientID.to_bytes(2, byteorder='big') + SERVERID.to_bytes(2, byteorder='big') + self.seqnum.to_bytes(2, byteorder='big') + len(text).to_bytes(2, byteorder='big') # Normal header of a MSG type, but using a MSGAP type instead
		message += destinyNickname.encode('ascii') + '-'.encode('ascii') + text # Concatenate the destiny nickname with the text message, separated by a '-'

		client.send(message)

		recvMessage = client.recv(BUFSIZE)

		if recvMessage[0:2] == MessageTypes.getMessageType('OK'):
			self.seqnum += 1
			print("Message delivered.")

		elif recvMessage[0:2] == MessageTypes.getMessageType('ERRO'):
			print("ERROR!")

class HelpMenu:
	def printHelpMenu():
		print('\nHelp Menu\n')
		print('Commands available:\n')
		print('> Print your client id:\noi\n')
		print('> Create a nickname for your client:\noiap nickname\nExample:\noiap ronald\n')
		print('> Print your client nickname:\noiap\n')
		print('> Request a list of all connected clients:\ncreq\n')
		print('> Request a list of all connected clients which has a nickname registered:\ncreqap\n')
		print('> Send a message to a client using his id:\nmsg to id - text\nExample:\nmsg to 3 - Hello World!\n')
		print('> Send a message to a client using his nickname:\nmsgap to id - text\nExample:\nmsgap to ronald - Hello World!\n')
		print('> Send a message to every connected client (broadcast):\nmsg to 0 - text\nExample:\nmsg to 0 - Hello World!\n')
		print('> Close the server connection and finish the client:\nflw\n\n')

host = sys.argv[1] # Server address received by command line argument
port = int(sys.argv[2]) # Server port received by command line argument

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Alocate a socket using TCP protocol and IPv4

client.connect((host, port)) # Connect the client to the server
print("Successfully connected on %s:%d" %(host, port))

chat = Communication() # Create an object of Communication to store all the data and methods of this specific client on the client side

chat.sendOI(client) # Send an OI message to the server, so it outputs the client ID

inputList = [client, sys.stdin] # Possible input list for the client side

active = True # Flag for the client to continue running

while active:
	inputSockets, outputSockets, error = select.select(inputList, inputList, []) # Get all the ready inputSockets and outputSockets

	for sock in inputSockets: # For each socket to be read

		if sock == client: # If the socket is the client socket, tries to receive a message from the server
			recvMessage = client.recv(BUFSIZE)

			if recvMessage[0:2] == MessageTypes.getMessageType('FLW'): # If the received message is a FLW type
				chat.sendFLW(client)
				active = False # Sets the running flag to be False, so the client will shutdown

			else:
				print("Message from [%d]:" %(int.from_bytes(recvMessage[2:4], byteorder='big')), end=' ')

				print(recvMessage[10:].decode())

				print('')

				chat.sendOK(client)

		elif sock == sys.stdin: # If the socket is the sys.stdin, tries to receive a command
			data = sys.stdin.readline().split('\n')[0] # Gets the command line from the sys.stdin input, without the '\n'
			data = data.split(' ') # Split the data from the sys.stdin input to be easier to analyze

			if data[0].upper() == 'OI': # If the received command is a OI type
				chat.sendOI(client)

			elif data[0].upper() == 'FLW': # If the received command is a FLW type
				chat.sendFLW(client)
				active = False # Sets the running flag to be False, so the client will shutdown

			elif data[0].upper() == 'CREQ': # If the received command is a CREQ type
				chat.sendCREQ(client)

			elif data[0].upper() == 'MSG': # If the received command is a MSG type
				text = " ".join(data[4:]).encode('ascii') # Joins all the text message into a text variable, separating each string by a space and encoding it to ascii
				chat.sendMSG(client, int(data[2]), text)

			elif data[0].upper() == 'OIAP': # If the received command is a OIAP type
				if data[1:]:
					nickname = " ".join(data[1:]).encode('ascii') # Joins all the nickname message into a nickname variable, separating each string by a space and encoding it to ascii
					chat.sendOIAP(client, nickname)
				else:
					chat.sendOIAP(client)

			elif data[0].upper() == 'CREQAP': # If the received command is a CREQAP type
				chat.sendCREQAP(client)

			elif data[0].upper() == 'MSGAP': # If the received command is a MSGAP type
				text = " ".join(data[4:]).encode('ascii') # Joins all the text message into a text variable, separating each string by a space and encoding it to ascii
				chat.sendMSGAP(client, data[2], text)

			elif data[0].upper() == 'HELP': # If the command is a help type
				HelpMenu.printHelpMenu() # Prints the help menu in the command terminal

			print('')


client.close() # Close the client socket connection