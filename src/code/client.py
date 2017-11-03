import sys
import socket
import select
import binascii

SERVERID = 65535 # ID do servidor = 65535
BUFSIZE = 400 # Maximum buffer size

class MessageTypes:
	def getMessageType(type):
		messageTypes = {
						'OK': (1).to_bytes(2, byteorder='big'),
						'ERRO': (2).to_bytes(2, byteorder='big'),
						'OI': (3).to_bytes(2, byteorder='big'),
						'FLW': (4).to_bytes(2, byteorder='big'),
						'MSG': (5).to_bytes(2, byteorder='big'),
						'CREQ': (6).to_bytes(2, byteorder='big'),
						'CLIST': (7).to_bytes(2, byteorder='big')
						}

		return messageTypes[type]


class Communication:
	def __init__(self):
		self.clientID = 0
		self.seqnum = 0

	def headerConstructor(self, type, destiny):
		return MessageTypes.getMessageType(type) + self.clientID.to_bytes(2, byteorder='big') + destiny.to_bytes(2, byteorder='big') + self.seqnum.to_bytes(2, byteorder='big')

	def sendOK(self, client):
		message = self.headerConstructor('OK', SERVERID)
		client.send(message)

	def sendOI(self, client):
		message = self.headerConstructor('OI', SERVERID)
		client.send(message)
		recvMessage = client.recv(BUFSIZE)

		if recvMessage[0:2] == MessageTypes.getMessageType('OK'):
			self.clientID = int.from_bytes(recvMessage[4:6], byteorder='big')
			self.seqnum += 1
			print("Connected successfully! Your ID is:", self.clientID)

	def sendFLW(self, client):
		message = self.headerConstructor('FLW', SERVERID)
		client.send(message)
		recvMessage = client.recv(BUFSIZE)

		if recvMessage[0:2] == MessageTypes.getMessageType('OK'):
			client.close()
			print("Connection closed successfully!")

	def sendCREQ(self, client):
		message = self.headerConstructor('CREQ', SERVERID)
		client.send(message)
		recvMessage = client.recv(BUFSIZE)

		if recvMessage[0:2] == MessageTypes.getMessageType('CLIST'):
			numberClients = int.from_bytes(recvMessage[8:10], byteorder='big')
			print("Number of connected clients:",numberClients)

			for i in range(1,numberClients+1):
				print(int.from_bytes(recvMessage[(8+i*2):(10+i*2)], byteorder='big'), end=' ')
			print('')

		message = self.headerConstructor('OK', SERVERID)
		client.send(message)

	def sendMSG(self, client, destiny, text):
		message = self.headerConstructor('MSG', destiny)
		message += len(text).to_bytes(2, byteorder='big')

		for c in text:
			message += int(c).to_bytes(1, byteorder='big')

		client.send(message)

		recvMessage = client.recv(BUFSIZE)

		if recvMessage[0:2] == MessageTypes.getMessageType('OK'):
			print("Message delivered.")

		elif recvMessage[0:2] == MessageTypes.getMessageType('ERRO'):
			print("ERROR!")


host = sys.argv[1]
port = int(sys.argv[2])

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

client.connect((host, port))
print("Successfully connected on %s:%d" %(host, port))

chat = Communication()

chat.sendOI(client)

inputList = [client, sys.stdin]

active = True

while active:
	inputSockets, outputSockets, error = select.select(inputList, inputList, [])

	for sock in inputSockets:

		if sock == client:
			recvMessage = client.recv(BUFSIZE)

			print("Message from [%d]:" %(int.from_bytes(recvMessage[2:4], byteorder='big')), end=' ')

			print(recvMessage[10:].decode())

			print('')

			chat.sendOK(client)

		elif sock == sys.stdin:
			data = sys.stdin.readline().split('\n')[0]
			data = data.split(' ')

			if data[0].upper() == 'OI':
				chat.sendOI(client)

			elif data[0].upper() == 'FLW':
				chat.sendFLW(client)
				active = False

			elif data[0].upper() == 'CREQ':
				chat.sendCREQ(client)

			elif data[0].upper() == 'MSG':
				text = " ".join(data[4:]).encode('ascii')
				chat.sendMSG(client, int(data[2]), text)


client.close()