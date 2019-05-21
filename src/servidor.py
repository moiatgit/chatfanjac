#! /usr/bin/env python3

"""
    Implementació d'un servidor de xat
"""

import sys
import socket
import threading
import logging
import queue
import time

# Mida màxima dels missatges a intercanviar entre el client i el servidor
MIDA_MISSATGE = 1024

# Nombre màxim de connexions simultànies acceptades
MAXIM_CONNEXIONS = 10

# Temps d'espera en les operacions d'entrada/sortida amb les connexions (en segons)
MAXIM_ESPERA_CONNEXIO = 2

# Constants per indicar el resultat d'una operació d'entrada/sortida amb sockets
RESULTA_OK = 0          # operació realitzada amb éxit
RESULTA_ERROR = 1       # operació no realitzada: s'ha produït un error
RESULTA_TIMEOUT = 2     # operació no realitzada: s'ha superat el temps


def principal(host, port):

    logging.info("Inici del servidor de xat")

    # socket de servidor
    servidor = arrenca_servidor(host, port)
    if not servidor:
        print("No s'ha aconseguit arrencar el servidor amb %s:%s" % (host, port))

    # marca de finalització
    finalitzacio = threading.Event()

    # missatges pendents
    missatges = queue.Queue()

    # participants del xat
    # clau: socket del participant. valor: (nom, es_actiu)
    participants = dict()

    # arrenca l'enviament de missatges
    llenca_fil_enviament_de_missatges(participants, missatges, finalitzacio)

    # arrenca el servei
    llenca_fil_gestio_de_peticions(servidor, participants, missatges, finalitzacio)

    # processa comandes de consola
    processa_comandes(participants, finalitzacio)
    logging.info("Finalització de l'execució de l'aplicació de servidor")


def arrenca_servidor(host, port):
    """ Crea la connexió del servidor  la configura
        Si tot ha anat bé, retona la connexió. None altrament
    """
    try:
        connexio = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        connexio.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        connexio.bind((host, port))
        connexio.settimeout(MAXIM_ESPERA_CONNEXIO)
        connexio.listen(MAXIM_CONNEXIONS)
        return connexio
    except OSError as e:
        logging.error("Error intentant crear el servidor amb %s:%s. Excepció (%s): %s" % (
                            host, port,
                            e.errno, e.strerror))
        return None


def llenca_fil_enviament_de_missatges(participants, missatges, finalitzacio):
    """ llença el fil d'execució que realitzarà l'enviament dels missatges als participants del xat """
    threading.Thread(target=envia_missatges, args=(participants, missatges, finalitzacio, )).start()
    logging.info("Llençat el fil d'enviament de missatges")


def llenca_fil_gestio_de_peticions(servidor, participants, missatges, finalitzacio):
    """ llença el fil d'execució que gestionarà les peticions de connexió dels participants del xat """
    threading.Thread(target=gestiona_peticions, args=(servidor, participants, missatges, finalitzacio)).start()


def envia_missatges(participants, missatges, finalitzacio):
    """ Aquesta és la funció que envia els missatges als participants

        Els missages venen a la cua de missatges en forma de tuples (destinatari, missatge)

        Si el destinatari no es troba a la llista de participants, o està marcat com inactiu, s'ignora
        Si no es pot enviar el missatge, es marca el participant com inactiu.
    """
    while not finalitzacio.isSet() or not missatges.empty():
        if missatges.empty():   # ens esperem una mica
            time.sleep(1)
            continue
        try:
            destinatari, missatge = missatges.get(MAXIM_ESPERA_CONNEXIO)
        except queue.Empty:
            continue
        missatges.task_done()
        try:
            adressa = destinatari.getpeername()   # comprovem que el destinatari continua connectat
        except OSError:
            # el participant està desconnectat
            participants.pop(destinatari, None)
            continue
        nom, es_actiu = participants.get(destinatari, (None, False))
        if not es_actiu:                    # ignora els participants no actius
            continue
        resultat = envia(destinatari, missatge)
        if resultat != RESULTA_OK:
            participants[destinatari] = (nom, False)    # queda marcat com a innactiu
            logging.info("Participant marcat com a innactiu %s:%s" % adressa)
            continue
    logging.info("Finalitza la gestió d'enviaments de missatges")


def gestiona_peticions(servidor, participants, missatges, finalitzacio):
    """ Aquesta és la funció que gestiona les noves peticions del servidor

        Es manté escoltant noves peticions fins que es marqui la finalització o
        hi hagi algun problema de connexió """

    logging.info("Iniciada la gestió de peticions")

    while not finalitzacio.isSet():
        try:
            nova_connexio, adressa = servidor.accept()
            logging.info("Nova connexió des de l'adreça %s" % str(adressa))
            nova_connexio.settimeout(MAXIM_ESPERA_CONNEXIO)
            llenca_fil_gestio_participant(nova_connexio, participants, missatges, finalitzacio)
            logging.info("Llençat fil d'execució per gestionar el nou participant %s" % str(adressa))
        except socket.timeout:
            # ha passat el temps màxim d'espera. Tornem a comprovar si encara cal continuar
            pass
        except OSError:
            logging.warning("Perduda connexió del servidor")
            missatge = "Ha caigut el servidor de xat. No es podran acceptar nous participants"
            broadcast(participants, missatges, [], missatge)
            print(missatge)
            break

    # tanca el servidor
    if finalitzacio.isSet():
        servidor.close()
    logging.info("Finalitzada la gestió de peticions")


def llenca_fil_gestio_participant(connexio, participants, missatges, finalitzacio):
    """ llença el fil d'execució que gestionarà els missatges que enviï un parcicipant """
    threading.Thread(target=gestiona_participant, args=(connexio, participants, missatges, finalitzacio)).start()


def gestiona_participant(connexio, participants, missatges, finalitzacio):
    """
        Aquesta és la funció que gestiona les comunicacions que envia un
        participant a traves de la connexió fins que la marca de finalització
        s'estableix
    """
    try:
        adressa = connexio.getpeername()
    except OSError:
        # la connexió està tancada
        return

    logging.info("Iniciada gestió per nou participant %s:%s" % adressa)

    # obté el nom del participant
    resultat, nom = rep(connexio)
    if resultat != RESULTA_OK:    # no s'ha aconseguit el nom i es finalitza l'execució
        logging.warning("No s'aconsegueix obtenir el nom del participant %s:%s. Finalitzat." % adressa)
        connexio.close()
        return

    # envia missatge de benvinguda
    missatge = "Hola %s. Acabes d'entrar a la sala de xat de Fanjac. " \
               "De moment hi ha %s participants" % (nom, len(participants) + 1)
    resultat = envia(connexio, missatge)
    if resultat != RESULTA_OK:
        logging.info("No s'aconsegueix enviar la benvinguda al participant %s. Finalitzat." % str((connexio.getpeername(), nom)))
        connexio.close()
        return

    # afegeix el nom del nou participant a la sala de participants
    participants[connexio] = (nom, True)
    logging.info("Nou participant %s a %s:%s" % (nom, adressa[0], adressa[1]))

    # envia a la resta de participants la notificació del nou participant
    missatge = "S'ha afegit %s. Ara ja sou %s participants" % (nom, len(participants))
    broadcast(participants, missatges, [connexio], missatge)

    # comença a gestionar els missatges que generi el participant
    while True:
        _, es_actiu = participants[connexio]
        if not es_actiu:    # el participant ha estat marcat com a innactiu
            break

        if finalitzacio.isSet():    # es tanca la sala de xat
            logging.info("Notificant la finalització al participant %s:%s" % adressa)
            missatge = "{quit}"
            missatges.put((connexio, missatge))
            break

        # recepció d'un nou missatge
        resultat, missatge = rep(connexio)
        if resultat == RESULTA_TIMEOUT: # temps exhaurit. Tornem-hi
            continue

        if resultat == RESULTA_ERROR:
            logging.warning("Perduda la connexió amb el participant %s:%s" % adressa)
            participants[connexio]=(nom, False) # marca com a inactiu
            # envia notificació de finalització de participant
            missatge = "S'ha perdut la connexió amb %s" % nom
            broadcast(participants, missatges, [connexio], missatge)
            break

        if missatge == '{quit}':
            logging.info("Rebuda petició de sortida del participant %s:%s" % adressa)
            participants[connexio]=(nom, False) # marca com a inactiu
            # envia notificació de finalització de participant
            missatge = "%s abandona la sala de xat" % nom
            broadcast(participants, missatges, [connexio], missatge)
            break

        # reenvia el missatge a la resta de participants
        reenviament = "[%s] %s" % (nom, missatge)
        broadcast(participants, missatges, [connexio], reenviament)

    time.sleep(1)   # deixem un temps perquè es pugui enviar els darrers missatges
    try:
        connexio.close()
    except OSError:
        pass
    participants.pop(connexio, None)
    logging.info("Finalitzada l'execució del participant %s:%s" % adressa)


def envia(connexio, missatge):
    """ Tracta d'enviar el missatge al participant."""
    try:
        connexio.sendall(bytes(missatge, "utf8"))
        return RESULTA_OK
    except socket.timeout:
        return RESULTA_TIMEOUT
    except OSError as e:
        return RESULTA_ERROR


def rep(connexio):
   """ obté un missatge del participant i es retorna
       El resultat és la tupla (resultat, missatge) """
   try:
       missatge = connexio.recv(MIDA_MISSATGE).decode("utf8")
       if len(missatge) == 0:
           return (RESULTA_ERROR, '')
       return (RESULTA_OK, missatge.strip())
   except socket.timeout:
       return (RESULTA_TIMEOUT, None)
   except OSError:
       return (RESULTA_ERROR, None)


def broadcast(participants, missatges, excepcions, missatge):
    """ afegeix als missatges pendents un enviament per cada participant
        excepte els indicats com a excepcions """
    for participant in participants:
        if participant in excepcions:
            continue
        missatges.put((participant, missatge))


def processa_comandes(participants, finalitzacio):
    """ processa les comandes que es reben de consola. """
    logging.info("Inici de processament de comandes")
    while not finalitzacio.isSet():
        comanda = input("Què vols fer? (ajuda): ").strip()
        if len(comanda) == 0:
            continue
        if  'ajuda'.startswith(comanda):
            print("Les comandes disponibles són:")
            print("\tajuda: mostra aquesta ajuda")
            print("\tquants: mostra quants participants estan actius")
            print("\tqui: mostra la llista de participants")
            print("\tfinalitza: finalitza el xat")
        elif 'quants'.startswith(comanda):
            print("El nombre de participants en aquest moment és %s" % len(participants))
        elif 'qui'.startswith(comanda):
            if len(participants) == 0:
                print("No hi ha cap participant en aquests moments")
            else:
                print("Els participants actuals són")
                for participant in participants:
                    nom, estat = participants.get(participant, ('', False))
                    print("\t%s (actiu: %s)" % (nom, estat))
        elif 'finalitza'.startswith(comanda):
            logging.info("Marcant l'esdeveniment de finalització per petició de la usuària")
            finalitzacio.set()
        else:
            print("Ho sento. No t'entenc. Escriu 'ajuda' per veure les opcions disponibles")

    print("Finalitzada la sessió de xat")



def obte_ip_i_port(argv):
    """
        obté la host i el port de la llista d'arguments

        Si les dades no són correctes, finalitza l'execució
    """
    if len(argv) != 3:
        print("Ús: %s «host» «port»" % argv[0])
        sys.exit()

    if not argv[2].isdigit() or not (1024 < int(argv[2]) <= 65535):
        print("ERROR: el port ha de ser un valor numèric entre 1025 i 65535")
        sys.exit()

    host = argv[1]
    port = int(argv[2])

    return (host, port)


if __name__ == '__main__':
    logging.basicConfig(filename="%s.log" % sys.argv[0],level=logging.DEBUG, format="%(asctime)s %(levelname)s: %(message)s")

    host, port = obte_ip_i_port(sys.argv)

    principal(host, port)


