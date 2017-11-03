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
	def headerConstructor(type, destiny, seqnum):
		return MessageTypes.getMessageType(type) + SERVERID + destiny.to_bytes(2, byteorder='big') + seqnum.to_bytes(2, byteorder='big')

	def sendOK(clientSocket):
		message = headerConstructor('OK', clientSocket.fileno(), 0)
		clientSocket.send(message)

host = '127.0.0.1'
port = int(sys.argv[1])

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

server.bind((host, port))
print("Server started and listening.")

server.listen(255)

hostList = [server, sys.stdin]

while 1:
	inputSockets, outputSockets, error = select.select(hostList, hostList, [])

	for sock in inputSockets:

		if sock == server:
			(clientSocket, address) = server.accept()
			print("Connected on client %d from %s." %(clientSocket.fileno(), address))

			hostList.append(clientSocket)
			print(hostList)

			recvMessage = clientSocket.recv(BUFSIZE)

			message = Communication.sendOK(clientSocket)




			print(inputSockets)