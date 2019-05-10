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


def gestiona_connexio():
    """Handles receiving of messages."""
    while True:
        try:
            msg = rep()
            if not msg or msg == '{quit}':
                print("XXX després de rep()")
                break
            print(msg)
            print(PROMPT, end='')
        except OSError:
            print("S'ha trencat la connexió amb el servidor")
            break
    print("XXX finalitzat gestiona_connexio()")

def rep():
    """ obté un missatge del socket del client i el retorna com a string """
    return socket_servidor.recv(MIDA_MISSATGE).decode("utf8").strip()

def send(missatge):  # event is passed by binders.
    """Handles sending of messages."""
    try:
        socket_servidor.send(bytes(missatge, "utf8"))
        return True
    except:
        print("S'ha perdut la connexió amb el servidor")
        return False


receive_thread = Thread(target=gestiona_connexio)
receive_thread.start()

print("Connectat al servidor")
nom = input("Indica el teu nom o àlies: ")
send(nom)
while receive_thread.is_alive():
    msg = input("%s" % PROMPT)
    correcte = send(msg)
    if msg == "{quit}" or not correcte:
        socket_servidor.close()
        break

print("Finalitzada la sessió")

