#!/ur/bin/env python3
"""
    Implementació d'un servidor de chat

    TODO:
    - more modularity
    - consider what happens when the connexion is lost before receiving client name
    - consider broadcasting close connection when server is down
    - check how to discover server ip or ask for it when launching
    - when closing connection (ctr-c) it keeps running.
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

clients = {}            # clau: client valor: (nom, adreça)
desconnectats = set()   # clients pels que s'ha tancat la connexió

def arrenca_servidor(host, port):
    """ arrenca i retorna un servidor en localhost i el port indicat """
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind((host, port))
    servidor.listen(MAXIM_CONNEXIONS)
    return servidor

def rep(client_socket):
    """ obté un missatge del socket del client i el retorna com a string """
    return client_socket.recv(MIDA_MISSATGE).decode("utf8").strip()

def envia(client_socket, missatge):
    """ envia un missatge a un client """
    try:
        client_socket.send(bytes(missatge, "utf8"))
    except (BrokenPipeError, ConnectionResetError):
        print("Perduda la connexió amb %s@%s" % clients[client_socket])
        desconnectats.add(client_socket)

def gestiona_client(client_socket, client_address):
    """ Gestiona la connexió d'un client """
    envia(client_socket, "Benvingut/benvinguda al nostre xat! " +
                         "Escriu el teu nom i prem enter.")
    nom_participant = rep(client_socket)
    envia(client_socket,"Quan vulguis sortir del xat, escriu {quit}.")
    clients[client_socket] = (nom_participant, client_address)
    broadcast("Ha entrat al xat!", client_socket)
    print("La connexió %s:%s correspon a %s" % (client_address[0], client_address[1], nom_participant))
    while True:
        msg = rep(client_socket)
        if msg != "{quit}":
            broadcast(msg, client_socket)
        else:
            client_socket.close()
            print("Finalitzada la connexió amb el client %s" % nom_participant)
            break
    desconnectats.add(client_socket)
    broadcast("Ha abandonat el xat.", client_socket)
    print("Finalitzat client " + nom_participant)

def broadcast(msg, origen=None):
    """ envia a tots els clients excepte a l'origen si està establert """
    print("Enviant a tothom el missatge %s: %s" % ("de %s" % clients[origen][0] if origen else "", msg))
    for client_socket in clients:
        if client_socket == origen:
            continue
        if client_socket in desconnectats:
            continue
        if origen:
            missatge = "%s: %s" % (clients[origen][0], msg)
        else:
            missatge = msg
        envia(client_socket, missatge)


try :
    servidor = arrenca_servidor('', port)
    print("Esperant connexions des del port %s" % port)
    while True:
        client_socket, client_address = servidor.accept()
        print("Nova connexió des de %s:%s." % client_address)
        Thread(target=gestiona_client, args=(client_socket, client_address)).start()
except KeyboardInterrupt as e:
    broadcast('{quit}')
    servidor.close()
    print("Servidor finalitzat correctament")


