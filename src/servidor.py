#!/ur/bin/env python3
"""
    Implementació d'un servidor de xat

    La implementació consisteix en tres tipus de fils d'execució:

    - el fil principal
      - obté les dades de configuració del servei (ip i port)
      - llença el fil de gestió de peticions
      - rep i processa comandes de consola
      - crea i marca l'esdeveniment (threading.Event) de finalització per que la resta de fils
        finalitzin la seva execució

    - el fil de gestió de peticions (executa la funció gestiona_peticions())
      - crea el socket de servidor
      - en cas que hi hagi problemes per crear el socket, marca l'esdeveniment de finalització
      - escolta el socket de servidor per noves peticions de clients per afegir-se al xat
      - en cas que hi hagi problemes per escoltar del socket, marca l'esdeveniment de finalització
      - llença un nou fil de gestió de participant per cada nou client
      - finalitza quan l'esdeveniment de finalització és marcat
      - tanca el servidor

    - el fil de gestió de participant (executa la funció gestiona_participant())
      - escolta el socket d'un participant per obtenir el nom
      - en cas que tingui problemes per rebre el nom del participant. finalitza execució del fil
      - informa al nou participant que ha estat admés al xat
      - presenta el nou participant a la resta de participants actius del xat
      - afegeix el nou participant (amb el seu socket i nom) a la llista de participants actius al xat
      - escolta el socket del participant per nous missatges del participant
      - per cada missatge del participant, reenvia el missatge a la resta
      - quan rep el missatge de finalització per part del participant,
        - elimina el participant de la llista de participants actius
        - notifica la resta de participants que aquest ha abandonat el xat
        - finalitza l'execució del fil
      - quan l'esdeveniment de finalització és marcat,
        - notifica el participant que el xat es tanca
        - finalitza l'execució del fil
      - si en algun moment perd la connexió amb el participant,
        - elimina el participant de la llista de participants actius
        - notifica la resta de participants que aquest ha perdut la connexió
        - finalitza l'execució del fil
      - en finalitzar l'execució del fil, tanca el socket

"""

import sys
import socket
import threading
import logging

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


def arrenca_servidor(ip, port, finalitzacio):
    """ intenta arrencar el servidor en la ip i ports. Si no ho
        aconsegueix, marca la finalització de l'execució """
    try:
        connexio = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        connexio.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        connexio.bind((ip, port))
        connexio.settimeout(MAXIM_ESPERA_CONNEXIO)
        connexio.listen(MAXIM_CONNEXIONS)
        return connexio
    except OSError as e:
        print("ERROR: no es pot arrencar el servidor. (erno %s): %s" % (e.errno, e.strerror))
        finalitzacio.set()



def envia(connexio, missatge):
    """ Tracta d'enviar el missatge al participant.
        Retorna cert si ho aconsegueix. Fals altrament. """
    try:
        connexio.send(bytes(missatge, "utf8"))
        return RESULTA_OK
    except socket.timeout:
        return RESULTA_TIMEOUT
    except OSError:
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


def broadcast(participants, missatge, excepte = []):
    """ envia el missatge a tots els participants, excepte als que apareguin a
        la llista d'excepcions
    """
    logging.info("Enviant missatge a tothom %s" % missatge)
    for connexio in participants:
        if connexio in excepte:  # ignorem els participants a exceptuar
            continue
        resultat = envia(connexio, missatge)
        if resultat != RESULTA_OK:
            logging.warning("Perduda la connexió amb el participant %s" % participant[connexio])
            connexio.close()
            del(participants[connexio])


def gestiona_participant(connexio, participants, finalitzacio):
    """ 
        Aquesta és la funció que gestiona les comunicacions que envia un
        participant a traves de la connexió fins que la marca de finalització
        s'estableix
    """
    logging.info("Iniciada gestió per nou participant %s" % participants[connexio])

    # obté el nom del participant
    resultat, nom = rep(connexio)
    if resultat != RESULTA_OK:    # no s'ha aconseguit el nom i es finalitza l'execució
        logging.warning("No s'aconsegueix obtenir el nom del participant %s. Finalitzat." % participants[connexio])
        connexio.close()
        del(participants[connexio])
        return

    # afegeix el nom del nou participant a la sala de participants
    participants[connexio] = (participants[connexio][0], nom)
    logging.info("Vinculat el nou participant amb el seu nom %s" % participants[connexio])

    # envia missatge de benvinguda
    missatge = "Hola %s. Acabes d'entrar a la sala de xat de Fanjac. " \
               "De moment hi ha %s participants" % len(participants)
    resultat = envia(connexio, missatge)
    if resultat != RESULTA_OK:
        logging.warning("No s'aconsegueix enviar notificació d'acceptació al participant %s. Finalitzat." % participants[connexio])
        del(participants[connexio])
        return

    # envia a la resta de participants la notificació del nou participant
    missatge = "S'ha afegit %s. Ara ja sou %s participants" % (nom, len(participants))
    broadcast(participants, missatge, excepte=[connexio])

    # comença a gestionar els missatges que generi el participant
    while not finalitzacio.isSet():
        resultat, missatge = rep(connexio)
        if resultat == RESULTA_TIMEOUT:
            # s'ha exhaurit el temps, donem-li una altra oportunitat
            continue

        if resutat == RESULTA_ERROR:
            logging.warning("Perduda la connexió amb el participant %s" % participants[connexio])
            missatge = "S'ha perdut la connexió amb %s" % participants[connexio][1]
            # envia notificació de finalització de participant
            broadcast(participants, missatge, excepte=[connexio])
            # elimina el participant de la llista de participants
            del(participants[connexio])
            break

        if missatge == '{quit}':
            logging.info("Rebuda petició de finalització per part del participant %s" % participants[connexio])
            missatge = "%s abandona la sala de xat" % participants[connexio][1]
            # envia notificació de finalització de participant
            broadcast(participants, missatge, excepte=[connexio])
            # elimina el participant de la llista de participants
            del(participants[connexio])
            break

        logging.info("Rebut missatge per part de participant %s: %s" % (participants[connexio][1], missatge))
        reenviament = "%s: %s" % (participants[connexio][1], missatge)
        broadcast(participants, missatge, excepte=[connexio])

    if finalització.isSet():
        missatge = "La sessió de xat ha estat tancada. Disculpa les molèsties."
        envia(connexio, missatge)

    logging.info("Finalitza la gestió del participant %s" % participants[connexio])
    connexio.close()


def gestiona_peticions(ip, port, participants, finalitzacio):
    """ Aquesta és la funció que gestiona les noves peticions del servidor

        Es manté escoltant noves peticions fins que es marqui la finalització o
        hi hagi algun problema de connexió """

    logging.info("Iniciada la gestió de peticions")
    # arrenca el servidor
    servidor = arrenca_servidor(ip, port, finalitzacio)

    # escolta peticions mentre no estigui marcada la finalització
    while not finalitzacio.isSet():
        try:
            nova_connexio, adressa = servidor.accept()
            logging.info("Nova connexió des de l'adreça %s" % str(adressa))
            nova_connexio.settimeout(MAXIM_ESPERA_CONNEXIO)
            participants[nova_connexio] = (adressa, None)      # de moment no sabem el nom del nou participant
            threading.Thread(target=gestiona_participant, args=(nova_connexio, participants, finalitzacio))
        except socket.timeout:
            # ha passat el temps màxim d'espera. Tornem a comprovar si encara cal continuar
            pass
        except OSError:
            logging.warning("Problemes amb la connexió del servidor. Es notifica a tots els usuaris")
            missatge = "Ha caigut el servidor de xat. No es podran acceptar nous participants"
            broadcast(participants, missatge)
            break

    # tanca el servidor
    servidor.close()
    logging.info("Finalitzada la gestió de peticions")


def llenca_fil_gestio_de_peticions(ip, port, participants, finalitzacio):
    """ llença el fil d'execució que gestionarà les peticions de connexió dels participants del xat """
    threading.Thread(target=gestiona_peticions, args=(ip, port, participants, finalitzacio, )).start()


def processa_comandes(participants, finalitzacio):
    """ processa les comandes que es reben de consola. """
    logging.info("Inici de processament de comandes")
    while not finalitzacio.isSet():
        comanda = input("Què vols fer? (ajuda): ")
        if comanda == 'ajuda':
            print("Les comandes disponibles són:")
            print("\tajuda: mostra aquesta ajuda")
            print("\tquants: mostra quants participants estan actius")
            print("\tfinalitza: finalitza el xat")
        elif comanda == 'quants':
            print("El nombre de participants en aquest moment és %s" % len(participants))
        elif comanda == 'finalitza':
            finalitzacio.set()
        else:
            print("Ho sento. No t'entenc. Escriu 'ajuda' per veure les opcions disponibles")

    print("Finalitzada la sessió de xat")

# configura el logging
logging.basicConfig(filename="%s.log" % sys.argv[0],level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logging.info("Arrenca l'aplicació de servidor")

# Obté la IP i el port on s'oferirà el servei
ip, port = obte_ip_i_port(sys.argv)
logging.info("Obtingudes les dades de connexió. IP: %s. Port: %s" % (ip, port))

# crea marca de finalització
# Aquesta marca permet indicar als diferents fils d'execució que cal finalitzar
finalitzacio = threading.Event()
logging.info("Creat esdeveniment de finalització")

# inicialitza la sala de xat
# S'implementa en forma de diccionari. La clau és la connexió amb el
# participant, i el valor és el nom del participant.
participants = dict()
logging.info("Inicialitzada la llista de participants")

# arrenca el servei
llenca_fil_gestio_de_peticions(ip, port, participants, finalitzacio)
logging.info("Llençat el fil de gestió de peticions")

# processa comandes de consola
processa_comandes(participants, finalitzacio)
logging.info("Finalització de l'execució de l'aplicació de servidor")
