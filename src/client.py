#! /usr/bin/env python3

"""
    Implementació d'un client de xat
"""

import socket
import sys
import threading
import logging

# Mida màxima dels missatges a intercanviar entre el client i el servidor
MIDA_MISSATGE = 1024

# Temps d'espera en les operacions d'entrada/sortida amb les connexions (en segons)
MAXIM_ESPERA_CONNEXIO = 2

# Constants per indicar el resultat d'una operació d'entrada/sortida amb sockets
RESULTA_OK = 0          # operació realitzada amb éxit
RESULTA_ERROR = 1       # operació no realitzada: s'ha produït un error
RESULTA_TIMEOUT = 2     # operació no realitzada: s'ha superat el temps


def obte_ip_port_i_nom(argv):
    """
        obté la host i el port del servidor, i el nom que tindrà el participant
        dins de la sala de xat.

        Si les dades no són correctes, finalitza l'execució
    """
    if len(argv) != 4:
        print("Ús: %s «host» «port» «nom participant»" % argv[0])
        sys.exit()

    if not argv[2].isdigit() or not (1024 < int(argv[2]) <= 65535):
        print("ERROR: el port ha de ser un valor numèric entre 1025 i 65535")
        sys.exit()

    host = argv[1]
    port = int(argv[2])
    nom = argv[3]

    return (host, port, nom)


def connecta_amb_servidor(host, port):
    """ Connecta amb el servidor en la host i port especificats.
        Si la connexió no és possible, ho notifica i finalitza l'execució.
    """
    try:
        connexio = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        connexio.settimeout(MAXIM_ESPERA_CONNEXIO)
        connexio.connect((host, port))
        return connexio
    except socket.timeout:
        logging.error("S'ha superat el temps d'espera màxim")
        print("En aquests moments no es pot connectar amb el servidor. Prova més tard")
        return None
    except OSError:
        logging.error("No s'ha pogut connectar amb el servidor")
        print("Hi ha problemes per connectar-se amb el servidor")
        return None


def gestiona_connexio(connexio, finalitzacio):
    """ Aquesta és la funció que gestiona la recepció de missatges per part de
        la connexió.

        Es manté escoltant noves peticions fins que es marqui la finalització o
        hi hagi algun problema de connexió.  """
    while not finalitzacio.isSet():
        resultat, missatge = rep(connexio)
        if resultat == RESULTA_TIMEOUT:
            # ha superat el temps d'espera, provem un altre cop
            continue
        if resultat == RESULTA_ERROR:
            # s'ha perdut la connexió amb el servidor
            finalitzacio.set()
            logging.info("Perduda la connexió amb el servidor")
            print("Perduda la connexió amb el servidor")
            break

        if missatge == "{quit}":
            finalitzacio.set()
            logging.info("Rebut missatge de finalització del servidor")
            print("El servidor s'ha tancat. Es finalitza aquesta sessió")
            break

        # rebut un missatge stàndard
        print(missatge)
        logging.info("Rebut missatge %s" % missatge)


    # tanca la connexió
    connexio.close()
    logging.info("Tancada la connexió")
    logging.info("Finalitza el fil de gestió de la connexió")


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
       logging.info("Rebut missatge %s" % missatge)
       return (RESULTA_OK, missatge.strip())
   except socket.timeout:
       return (RESULTA_TIMEOUT, None)
   except OSError:
       return (RESULTA_ERROR, None)


def llenca_fil_gestio_connexio(connexio, finalitzacio):
    """ llença el fil d'execució que gestionarà els missatges que es rebin del servidor """
    threading.Thread(target=gestiona_connexio, args=(connexio, finalitzacio)).start()


def processa_comandes(connexio, finalitzacio):
    """ processa les comandes que es reben de consola. """
    print("Introdueix els missatges que vulguis enviar a tothom. '{quit}' per abandonar el xat")
    while not finalitzacio.isSet():
        missatge = input().strip()
        if len(missatge) == 0:  # ignorem missatges amb només espais o buits
            continue
        resultat = envia(connexio, missatge)
        if resultat != RESULTA_OK:
            print("S'ha produït un error en contactar amb el servidor. Es tanca la sessió.")
            finalitzacio.set()
            logging.error("Error en enviar missatge al servidor")
            break
        if missatge == "{quit}":
            print("Has abandonat la sala de xat. Fins la propera.")
            finalitzacio.set()
            logging.info("El participant ha abandonat la sala de xat")
            break

def principal(host, port, nom):

    # crea marca de finalització
    # Aquesta marca permet indicar als diferents fils d'execució que cal finalitzar
    finalitzacio = threading.Event()
    logging.info("Creat esdeveniment de finalització")

    # Intentem la connexió amb el servidor
    connexio = connecta_amb_servidor(host, port)
    if not connexio:
        logging.error("No s'ha aconseguit connectar amb el servidor")
        return

    logging.info("Connectat amb el servidor")

    # Envia el nom del participant
    resultat = envia(connexio, nom)
    if resultat != RESULTA_OK:
        logging.error("No s'ha aconseguit enviar el nom al servidor")
        print("No s'ha pogut contactar correctament amb el servidor")
        connexio.close()
        return

    # Arrenca la connexió amb el servidor
    llenca_fil_gestio_connexio(connexio, finalitzacio)
    logging.info("Llençat el fil de gestió de connexió")

    # processa comandes de consola
    processa_comandes(connexio, finalitzacio)


    print("Finalitzada la sessió")
    logging.info("Finalitzada la sessió del participant %s" % nom)

if __name__ == '__main__':
    # configura el logging
    logging.basicConfig(filename="%s.log" % sys.argv[0],
            level=logging.INFO,
            format="%(asctime)s %(levelname)s: %(message)s")
    logging.info("Arrenca l'aplicació de client")

    # Obté la host i el port de connexió amb el servidor
    host, port, nom = obte_ip_port_i_nom(sys.argv)
    logging.info("Obtingudes les dades de connexió. host: %s. Port: %s, nom: %s" % (host, port, nom))

    principal(host, port, nom)

