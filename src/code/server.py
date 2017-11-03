import sys
import socket
import select

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
	def headerConstructor(type, destiny, seqnum):
		return MessageTypes.getMessageType(type) + SERVERID.to_bytes(2, byteorder='big') + destiny.to_bytes(2, byteorder='big') + seqnum.to_bytes(2, byteorder='big')

	def sendOK(clientSocket):
		message = Communication.headerConstructor('OK', clientSocket.fileno()-3, 0)
		clientSocket.send(message)

	def sendERRO(clientSocket):
		message = Communication.headerConstructor('ERRO', clientSocket.fileno()-3, 0)
		clientSocket.send(message)

	def sendCLIST(clientSocket, hostList):
		message = Communication.headerConstructor('CLIST', clientSocket.fileno()-3, 0)

		message += len(hostList[2:]).to_bytes(2, byteorder='big')

		for sock in hostList[2:]:
			message += (sock.fileno()-3).to_bytes(2, byteorder='big')

		clientSocket.send(message)

		recvMessage = clientSocket.recv(BUFSIZE)

		if recvMessage[0:2] == MessageTypes.getMessageType('OK'):
			return

	def sendMSG(origin, message, hostList):
		source = int.from_bytes(message[2:4], byteorder='big') + 3
		destiny = int.from_bytes(message[4:6], byteorder='big')

		if destiny > 0:
			destiny += 3

			for host in hostList:
				if host.fileno() == destiny:
					host.send(message)
					recvMessage = host.recv(BUFSIZE)

					if recvMessage[0:2] == MessageTypes.getMessageType('OK'):
						Communication.sendOK(origin)

					elif recvMessage[0:2] == MessageTypes.getMessageType('ERRO'):
						Communication.sendERRO(origin)
					return

			Communication.sendERRO(origin)

		else:
			valid = True
			for host in hostList:
				if host != origin:
					host.send(message)
					recvMessage = host.recv(BUFSIZE)

					if recvMessage[0:2] == MessageTypes.getMessageType('ERRO'):
						valid = False

			if valid:
				Communication.sendOK(origin)

			else:
				Communication.sendERRO(origin)


host = '127.0.0.1'
port = int(sys.argv[1])

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

server.bind((host, port))
print("Server started and listening.")

server.listen(255)

hostList = [server, sys.stdin]

active = True

while active:
	inputSockets, outputSockets, error = select.select(hostList, hostList[2:], [])

	for sock in inputSockets:

		if sock == server:
			(clientSocket, address) = server.accept()
			print("Connected on client %d from %s." %(clientSocket.fileno()-3, address))

			hostList.append(clientSocket)

		elif sock == sys.stdin:
			if sys.stdin.readline().split('\n')[0] == 'shutdown':
				active = False

		else:
			recvMessage = sock.recv(BUFSIZE)

			if recvMessage[0:2] == MessageTypes.getMessageType('MSG'):
				Communication.sendMSG(sock, recvMessage, hostList[2:])

			elif recvMessage[0:2] == MessageTypes.getMessageType('OI'):
				Communication.sendOK(sock)

			elif recvMessage[0:2] == MessageTypes.getMessageType('FLW'):
				Communication.sendOK(sock)
				sock.close()
				hostList.remove(sock)

			elif recvMessage[0:2] == MessageTypes.getMessageType('CREQ'):
				Communication.sendCLIST(sock, hostList)

server.close()