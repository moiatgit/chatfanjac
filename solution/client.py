#!/usr/bin/env python3
"""Script for Tkinter GUI chat client."""
import socket
import sys
from threading import Thread

MIDA_MISSATGE = 1024

PROMPT = '> '


socket_servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
if len(sys.argv) != 3:
    print("Ús: %s host port" % sys.argv[0])
    exit()
host = sys.argv[1]
port = int(sys.argv[2])
socket_servidor.connect((host, port))


def receive():
    """Handles receiving of messages."""
    while True:
        try:
            msg = socket_servidor.recv(MIDA_MISSATGE).decode("utf8")
            print(msg)
            print(PROMPT, end='')
        except OSError:
            print("S'ha trencat la connexió amb el servidor")
            break


def send(missatge):  # event is passed by binders.
    """Handles sending of messages."""
    socket_servidor.send(bytes(missatge, "utf8"))


receive_thread = Thread(target=receive)
receive_thread.start()

print("Connectat al servidor")
nom = input("Indica el teu nom o àlies: ")
send(nom)
while True:
    msg = input("%s" % PROMPT)
    send(msg)
    if msg == "{quit}":
        break

socket_servidor.close()
print("Finalitzada la sessió")

