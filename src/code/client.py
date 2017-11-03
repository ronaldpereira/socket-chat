import sys
import socket
import select

SERVERID = (65535).to_bytes(2, byteorder='big') # ID do servidor = 65535
BUFSIZE = 65535 # Maximum buffer size

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

	def headerConstructor(self, type, origin, destiny, seqnum):
		return MessageTypes.getMessageType(type) + origin.to_bytes(2, byteorder='big') + destiny.to_bytes(2, byteorder='big') + seqnum.to_bytes(2, byteorder='big')

	def sendOI(client):
		message = Communication.headerConstructor('OI', self.clientID, SERVERID, self.seqnum)
		client.send(message)
		recvMessage = client.recv(BUFSIZE)
		self.clientID = recvMessage[16:32]
		self.seqnum += 1


host = sys.argv[1]
port = int(sys.argv[2])

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

client.connect((host, port))
print("Successfully connected on %s:%d" %(host, port))

chat = Communication()