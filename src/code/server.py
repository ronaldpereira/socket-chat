import sys
import struct
import socket
import select
import queue

port = int(sys.argv[1])

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)