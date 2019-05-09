#!/ur/bin/env python3
"""
    Implementació d'un servidor de chat
"""

import sys
import socket
from threading import Thread


MIDA_MISSATGE = 1024
MAXIM_CONNEXIONS = 5


# Obté el port de connexió
if len(sys.argv) != 2:
    print("Ús: %s port" % sys.argv[0])
    sys.exit()

port = int(sys.argv[1])

# composa l'adreça en la que el servidor oferirà el servei
adresa = ('localhost', port)


# 
clients = {}
addresses = {}


# creem el socket de servidor
servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
servidor.bind(adresa)

def accept_incoming_connections():
    """Sets up handling for incoming clients."""
    while True:
        client, client_address = servidor.accept()
        print("%s:%s has connected." % client_address)
        client.send(bytes("Greetings from the cave!"+
                          "Now type your name and press enter!", "utf8"))
        addresses[client] = client_address
        Thread(target=handle_client, args=(client,)).start()

def handle_client(client):  # Takes client socket as argument.
    """Handles a single client connection."""
    name = client.recv(MIDA_MISSATGE).decode("utf8")
    welcome = 'Welcome %s! If you ever want to quit, type {quit} to exit.' % name
    client.send(bytes(welcome, "utf8"))
    msg = "%s has joined the chat!" % name
    broadcast(bytes(msg, "utf8"))
    clients[client] = name
    while True:
        msg = client.recv(MIDA_MISSATGE)
        if msg != bytes("{quit}", "utf8"):
            broadcast(msg, name+": ")
        else:
            client.send(bytes("{quit}", "utf8"))
            client.close()
            del clients[client]
            broadcast(bytes("%s has left the chat." % name, "utf8"))
            break

def broadcast(msg, prefix=""):  # prefix is for name identification.
    """Broadcasts a message to all the clients."""
    for sock in clients:
        sock.send(bytes(prefix, "utf8")+msg)


def main():
    servidor.listen(MAXIM_CONNEXIONS)
    print("Esperant connexions des del port %s" % port)
    accept_thread = Thread(target=accept_incoming_connections)
    accept_thread.start()
    accept_thread.join()
    servidor.close()


if __name__ == "__main__":
    main()
