#!/ur/bin/env python3
"""
    Implementació d'un servidor de chat
"""

import sys
import socket
from threading import Thread
import collections

# Mida màxima dels missatges a intercanviar entre el client i el servidor
MIDA_MISSATGE = 1024

# Nombre màxim de connexions simultànies acceptades
MAXIM_CONNEXIONS = 10

#class FanjacServer:
#    """ Aquesta classe implementa un servidor de sala de xat """
#
#
#    def __init__(self, ip, port):
#        """ inicia el servidor amb aquesta ip i port """
#        self.ip = ip
#        self.port = port
#        clients = {}             # clau: client valor: (nom, adreça)
#        desconnectats = set()    # clients pels que s'ha tancat la connexió
#        self._arrenca_servidor()
#
#
#class Participant:
#    """ Aquesta classe implementa un participant dins de la sala de xat """
#
#    def __init__(self)
#
#
#
#def envia(client_socket, missatge):
#    """ envia un missatge a un client """
#    try:
#        client_socket.send(bytes(missatge, "utf8"))
#    except (BrokenPipeError, ConnectionResetError):
#        print("Perduda la connexió amb %s@%s" % clients[client_socket])
#        desconnectats.add(client_socket)
#
#
#def gestiona_client(client_socket, client_address):
#    """ Gestiona la connexió d'un client """
#    envia(client_socket, "Benvingut/benvinguda al nostre xat! " +
#                         "Escriu el teu nom i prem enter.")
#    nom_participant = rep(client_socket)
#    envia(client_socket,"Quan vulguis sortir del xat, escriu {quit}.")
#    clients[client_socket] = (nom_participant, client_address)
#    broadcast("Ha entrat al xat!", client_socket)
#    print("La connexió %s:%s correspon a %s" % (client_address[0], client_address[1], nom_participant))
#    while True:
#        msg = rep(client_socket)
#        if msg != "{quit}":
#            broadcast(msg, client_socket)
#        else:
#            client_socket.close()
#            print("Finalitzada la connexió amb el client %s" % nom_participant)
#            break
#    desconnectats.add(client_socket)
#    broadcast("Ha abandonat el xat.", client_socket)
#    print("Finalitzat client " + nom_participant)
#
#
#def broadcast(msg, origen=None):
#    """ envia a tots els clients excepte a l'origen si està establert """
#    print("Enviant a tothom el missatge %s: %s" % ("de %s" % clients[origen][0] if origen else "", msg))
#    for client_socket in clients:
#        if client_socket == origen:
#            continue
#        if client_socket in desconnectats:
#            continue
#        if origen:
#            missatge = "%s: %s" % (clients[origen][0], msg)
#        else:
#            missatge = msg
#        envia(client_socket, missatge)
#


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


def arrenca_servidor(ip, port):
    """ intenta arrencar el servidor en la ip i ports. Si no ho
        aconsegueix, mostra un missatge i finalitza l'execució. """
    try:
        connexio = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        connexio.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        connexio.bind((ip, port))
        connexio.listen(MAXIM_CONNEXIONS)
        return connexio
    except OSError as e:
        print("ERROR: no es pot arrencar el servidor. (erno %s): %s" % (e.errno, e.strerror))
        sys.exit()


def treu_participant(participant, participants, missatge):
    """ treu el participant de la llista i notifica a la resta amb un missatge """
    print("Perduda la connexió amb %s" % participants[participant])

    # envia notificació de finalització de participant
    broadcast(participants, missatge, excepte=[participant])

    # elimina el participant de la llista de participants
    del(participants[participant])



def envia(participant, missatge, participants):
    """ Tracta d'enviar el missatge al participant.
        Si no ho aconsegueix, considera que s'ha perdut la connexió, 
        el treu de la llista de participants i notifica la resta de participants """
    try:
        participant.send(bytes(missatge, "utf8"))
    except (BrokenPipeError, ConnectionResetError):
        if participants[participant]:    # ja tenim nom del participant
            missatge = "Perduda la connexió amb %s" % participants[participant]
            treu_participant(participant, participants, missatge)


def rep(participant, participant):
   """ obté un missatge del participant
       Si no és possible obtenir el missatge del participant,es treu de la llista.
   """
   try:
       return participant.recv(MIDA_MISSATGE).decode("utf8").strip()
   except (BrokenPipeError, ConnectionResetError):
       if participants[participant]:    # ja tenim nom del participant
           missatge = "Perduda la connexió amb %s" % participants[participant]
           treu_participant(participant, participants, missatge)



def broadcast(participants, missatge, excepte = []):
    """ envia el missatge a tots els participants, excepte als que apareguin a
        la llista d'excepcions """
    for participant in participants:
        if participant in excepte:  # ignorem els participants a exceptuar
            continue
        envia(participant, missatge)


def gestiona_participant(connexio, participants, finalitzacio):
    """ gestiona les comunicacions que envia un participant a traves de la
        connexió fins que la marca de finalització s'estableix """

    # obté el nom del participant
    nom = rep(connexio)

    # afegeix el nou participant a la sala de participants
    participants[connexio] = nom

    # envia missatge de benvinguda
    missatge = "Hola. Acabes d'entrar a la sala de xat de Fanjac. " \
               "De moment hi ha %s participants" % len(participants)
    envia(connexio, missatge)

    # envia a la resta de participants la notificació del nou participant
    missatge = "S'ha afegit %s. Ara ja sou %s participants" % (nom, len(participants))
    broadcast(participants, missatge, excepte=[connexio])

    # comença a gestionar els missatges que generi el participant


def gestiona_peticions(servidor, participants, finalitzacio):
    """ es manté escoltant noves peticions fins que es marqui la finalització o
        hi hagi algun problema de connexió """
    while not finalitzacio.isSet():
        nova_connexio, adressa = servidor.accept()
        print("Nova connexió des de l'adreça %s" % adressa)
        participants[nova_connexio] = None      # de moment no sabem el nom del nou participant
        threading.Thread(target=gestiona_participant, args=(nova_connexio, participants, finalitzacio))


def inicia_servei(servidor, participants, finalitzacio):
    """ llença el fil d'execució que gestionarà les peticions de connexió dels participants del xat """
    threading.Thread(target=gestiona_peticions, args=(servidor, participants, finalitzacio, )).start()


# Obté la IP i el port on s'oferirà el servei
ip, port = obte_ip_i_port(sys.argv)

# arrenca el servidor
servidor = arrenca_servidor(ip, port)

# crea marca de finalització
# Aquesta marca permet indicar als diferents fils d'execució que cal finalitzar
finalitzacio = threading.Event()

# inicialitza la sala de xat
# S'implementa en forma de diccionari. La clau és la connexió amb el
# participant, i el valor és el nom del participant.
participants = dict()

# arrenca el servei
inicia_servei(servidor, participants, finalitzacio)

sys.exit()

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


