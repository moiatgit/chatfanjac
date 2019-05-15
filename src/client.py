#!/usr/bin/env python3
"""
    Implementació d'un client de xat

    La implementació consisteix en dos tipus de fils d'execució:

    - el fil principal
      - obté les dades de configuració de la connexió (ip, port i nom del participant)
      - realitza la connexió amb el servidor
      - envia el nom del participant
      - llença el fil de gestió dels missatges rebuts del servidor
      - rep i processa comandes de consola
      - crea i marca l'esdeveniment (threading.Event) de finalització per què
        la resta de fils finalitzin la seva execució

    - el fil de gestió de la connexió (executa la funció gestiona_connexio())
      - escolta el socket de connexió amb el servidor
      - en cas que tingui problemes per escoltar el socket, marca l'esdeveniment de finalització
      - en cas qeu rebi el missatge '{quit}', marca l'esdeveniment de finalització
      - mostra els missatges que va rebent
      - tanca la connexió en rebre l'esdeveniment de finalització

    
    Script for Tkinter GUI chat client."""
import socket
import sys
import threading
import logging

# Prompt que es mostrarà a la consola del client
PROMPT = '> '

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
        obté la ip i el port del servidor, i el nom que tindrà el participant
        dins de la sala de xat.

        Si les dades no són correctes, finalitza l'execució
    """
    if len(argv) != 4:
        print("Ús: %s «ip» «port» «nom participant»" % argv[0])
        sys.exit()

    if not argv[2].isdigit() or not (1024 < int(argv[2]) <= 65535):
        print("ERROR: el port ha de ser un valor numèric entre 1025 i 65535")
        sys.exit()

    ip = argv[1]
    port = int(argv[2])
    nom = argv[3]

    return (ip, port, nom)


def connecta_amb_servidor(ip, port):
    """ Connecta amb el servidor en la IP i port especificats.
        Si la connexió no és possible, ho notifica i finalitza l'execució.
    """
    try:
        connexio = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        connexio.settimeout(MAXIM_ESPERA_CONNEXIO)
        connexio.connect((ip, port))
        return connexio
    except socket.timeout:
        logging.error("S'ha superat el temps d'espera màxim")
        print("En aquests moments no es pot connectar amb el servidor. Prova més tard")
        sys.exit()
    except OSError:
        logging.error("No s'ha pogut connectar amb el servidor")
        print("Hi ha problemes per connectar-se amb el servidor")
        sys.exit()


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

        if missatge == "{quit}":
            logging.info("Rebut missatge de finalització del servidor")
            print("El servidor s'ha tancat. Es finalitza aquesta sessió")
            finalitzacio.set()
            break

        # rebut un missatge stàndard
        print(missatge)
        logging.info("Rebut missatge %s" % missatge)


    # tanca la connexió
    connexio.close()
    logging.info("Tancada la connexió")
    logging.info("Finalitza el fil de gestió de la connexió")


def envia(connexio, missatge):
    """ Tracta d'enviar el missatge al participant.
        Retorna cert si ho aconsegueix. Fals altrament. """
    try:
        connexio.send(bytes(missatge, "utf8"))
        logging.info("Enviat missatge %s" % missatge)
        return RESULTA_OK
    except socket.timeout:
        return RESULTA_TIMEOUT
    except OSError as e:
        logging.error(e.message)
        return RESULTA_ERROR


def rep(connexio):
   """ obté un missatge del participant i es retorna
       Si no és possible obtenir el missatge del participant, es retorna None
   """
   try:
       return (RESULTA_OK, connexio.recv(MIDA_MISSATGE).decode("utf8").strip())
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
        missatge = input("%s" % PROMPT)
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

# configura el logging
logging.basicConfig(filename="%s.log" % sys.argv[0],
        level=logging.INFO, 
        format="%(asctime)s %(levelname)s: %(message)s")
logging.info("Arrenca l'aplicació de client")

# Obté la IP i el port de connexió amb el servidor
ip, port, nom = obte_ip_port_i_nom(sys.argv)
logging.info("Obtingudes les dades de connexió. IP: %s. Port: %s, nom: %s" % (ip, port, nom))

# crea marca de finalització
# Aquesta marca permet indicar als diferents fils d'execució que cal finalitzar
finalitzacio = threading.Event()
logging.info("Creat esdeveniment de finalització")

# Intentem la connexió amb el servidor
connexio = connecta_amb_servidor(ip, port)
logging.info("Connectat amb el servidor")

# Envia el nom del participant
resultat = envia(connexio, nom)
if resultat != RESULTA_OK:
    logging.error("No s'ha aconseguit enviar el nom al servidor")
    print("No s'ha pogut contactar correctament amb el servidor")
    connexio.close()
    sys.exit()

# Arrenca la connexió amb el servidor
llenca_fil_gestio_connexio(connexio, finalitzacio)
logging.info("Llençat el fil de gestió de connexió")

# processa comandes de consola
processa_comandes(connexio, finalitzacio)


print("Finalitzada la sessió")
logging.info("Finalitzada la sessió del participant %s" % nom)

