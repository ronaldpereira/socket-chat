import sys
import socket
import select
import queue

host = '127.0.0.1'
port = int(sys.argv[1])

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

sock.bind((host, port))
print("Server started and listening.")

sock.listen(65534)

while 1:
	(clientSocket, adress) = sock.accept()
	print("Connected on a client.")

	message = clientSocket.recv(65535).decode()

	print(message)

	message = clientSocket.recv(65535).decode()

	print("Last message:"+message)