import sys
import socket
import select
import queue

host = sys.argv[1]
port = int(sys.argv[2])

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

sock.connect((host, port))
print("Successfully connected")

message = "Hello. I'm connected"

sock.send(message.encode())