#!/ur/bin/env python3
"""
    Implementació d'un servidor de chat
"""

import sys
import socket
from threading import Thread
import collections


MIDA_MISSATGE = 1024
MAXIM_CONNEXIONS = 5


# Obté el port de connexió
if len(sys.argv) != 2:
    print("Ús: %s port" % sys.argv[0])
    sys.exit()

port = int(sys.argv[1])

# composa l'adreça en la que el servidor oferirà el servei
adresa = ('localhost', port)

clients = {}        # clau: client valor: (nom, adreça)


# creem el socket de servidor
servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
servidor.bind(adresa)

def accept_incoming_connections():
    """Sets up handling for incoming clients."""
    while True:
        client_socket, client_address = servidor.accept()
        print("%s:%s has connected." % client_address)
        client_socket.send(bytes("Benvingut/benvinguda al nostre xat!\n"+
                          "Escriu el teu nom i prem enter.", "utf8"))
        Thread(target=handle_client, args=(client_socket, client_address)).start()

def handle_client(client_socket, client_address):
    """ Gestiona la connexió d'un client """
    name = client_socket.recv(MIDA_MISSATGE).decode("utf8").strip()
    welcome = 'Benvingut/benvinguda %s! Quan vulguis sortir del xat, escriu {quit}.' % name
    client_socket.send(bytes(welcome, "utf8"))
    msg = "%s ha entrat al xat!" % name
    broadcast(bytes(msg, "utf8"))
    clients[client_socket] = (name, client_address)
    while True:
        msg = client_socket.recv(MIDA_MISSATGE)
        if msg != bytes("{quit}", "utf8"):
            broadcast(msg, name+": ")
        else:
            client_socket.send(bytes("{quit}", "utf8"))
            client_socket.close()
            del clients[client_socket]
            broadcast(bytes("%s ha sortit del xat." % name, "utf8"))
            break

def broadcast(msg, prefix=""):  # prefix is for name identification.
    """Broadcasts a message to all the clients."""
    for sock in clients:
        sock.send(bytes(prefix, "utf8")+msg)


def main():
    servidor.listen(MAXIM_CONNEXIONS)
    print("Esperant connexions des del port %s" % port)
    while True:
        client_socket, client_address = servidor.accept()
        print("%s:%s has connected." % client_address)
        client_socket.send(bytes("Benvingut/benvinguda al nostre xat!\n"+
                          "Escriu el teu nom i prem enter.", "utf8"))
        Thread(target=handle_client, args=(client_socket, client_address)).start()

    print("Finalitzem el servidor")
    servidor.close()


if __name__ == "__main__":
    main()
