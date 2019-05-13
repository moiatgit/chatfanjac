#!/ur/bin/env python3
"""
    Implementació d'un servidor de chat
"""

import sys
import socket
from threading import Thread
import collections
import chatroomutils


class FanjacServer:
    """ Aquesta classe implementa un servidor de sala de xat """

    # Nombre màxim de connexions simultànies acceptades
    MAXIM_CONNEXIONS = 10

    def __init__(self, ip, port):
        """ inicia el servidor amb aquesta ip i port """
        self.ip = ip
        self.port = port
        clients = {}             # clau: client valor: (nom, adreça)
        desconnectats = set()    # clients pels que s'ha tancat la connexió
        self._arrenca_servidor()

    def _arrenca_servidor(self):
        """ intenta arrencar el servidor en la ip i ports. Si no ho
            aconsegueix, mostra un missatge i finalitza l'execució. """
        self.connexio = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connexio.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.connexio.bind((ip, port))
        self.connexio.listen(FanjacServer.MAXIM_CONNEXIONS)

    def _rep(self, participant):
        """ obté un missatge del participant """
        return participant.recv(chatroomutils.MIDA_MISSATGE).decode("utf8").strip()

class Participant:
    """ Aquesta classe implementa un participant dins de la sala de xat """

    def __init__(self)

def obte_ip_i_port(argv):
    """ 
        obté la ip i el port de la llista d'arguments

        Si les dades no són correctes, finalitza l'execució
    """
    if len(argv) != 3:
        print("Ús: %s «ip» «port»" % argv[0])
        sys.exit()

    if not argv[2].isdigit() or not (1024 < int(argv[2]) <= 65535):
        print("ERROR: el port ha de ser un valor numèric entre 1025 i 65535")
        sys.exit()

    ip = argv[1]
    port = int(argv[2])

    return (ip, port)



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


# Obté la IP i el port on s'oferirà el servei
ip, port = obte_ip_i_port(sys.argv)


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


