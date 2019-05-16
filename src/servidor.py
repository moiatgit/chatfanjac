#!/ur/bin/env python3
"""
    Implementació d'un servidor de xat

    La implementació consisteix en quatre tipus de fils d'execució:

    - el fil principal
      - obté les dades de configuració del servei (ip i port)
      - llença el fil d'enviament de missatges
      - llença el fil de gestió de peticions
      - rep i processa comandes de consola
      - crea la qua de missatges que permet comunicar els altres fils amb el fil d'enviament de missatges
      - crea i marca l'esdeveniment (threading.Event) de finalització per que la resta de fils
        finalitzin la seva execució

    - el fil de gestió de peticions (executa la funció gestiona_peticions())
      - crea el socket de servidor
      - en cas que hi hagi problemes per crear el socket, marca l'esdeveniment de finalització
      - escolta el socket de servidor per noves peticions de clients per afegir-se al xat
      - en cas que hi hagi problemes per escoltar del socket, marca l'esdeveniment de finalització
      - llença un nou fil de gestió de participant per cada nou client
      - finalitza quan l'esdeveniment de finalització és marcat
      - tanca el socket de servidor

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
        - tanca la connexio del participant
        - finalitza l'execució del fil
      - quan l'esdeveniment de finalització és marcat,
        - notifica el participant que el xat es tanca
        - tanca la connexio del participant
        - finalitza l'execució del fil
      - si en algun moment perd la connexió amb el participant,
        - notifica la resta de participants que aquest ha perdut la connexió
        - tanca la connexio del participant
        - finalitza l'execució del fil
      - en finalitzar l'execució del fil, tanca el socket

"""

import sys
import socket
import threading
import logging
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
        logging.info("Marcant l'esdeveniment de finalització per impossibilitat de crear la connexió")
        finalitzacio.set()


def envia(connexio, missatge):
    """ Tracta d'enviar el missatge al participant.
        Retorna cert si ho aconsegueix. Fals altrament. """
    try:
        connexio.send(bytes(missatge, "utf8"))
        return RESULTA_OK
    except socket.timeout:
        return RESULTA_TIMEOUT
    except OSError as e:
        return RESULTA_ERROR

def broadcast(participants, missatge, excepte = []):
    """ envia el missatge a tots els participants, excepte als que apareguin a
        la llista d'excepcions.
        Si no pot enviar el missatge a algun dels participants, tanca la seva connexió
        però no el treu de la llista de participants actius. Es deixa aquesta acció al fil
        de gestió del participant.
    """
    logging.info("Enviant missatge a tothom %s" % missatge)
    for connexio in list(participants.keys()):
        if connexio in excepte:  # ignorem els participants a exceptuar
            continue
        resultat = envia(connexio, missatge)
        if resultat != RESULTA_ERROR:
            logging.info("broadcast() desconnecta el participant %s" % str(connexio.getpeername()))
            connexio.close()


def rep(connexio):
   """ obté un missatge del participant i es retorna
       Si l'espera supera el temps mæxim, retorna com a resultat RESULTA_TIMEOUT
       Si no és possible obtenir el missatge del participant, ja sigui per que es produeix una excepció o perquè el missatge és la cadena buida, es retorna RESULTA_ERROR
       Si tot ha anat correcte, el resultat és RESULTA_OK
       El resultat és la tupla (resultat, missatge)
   """
   logging.info("Intentant rebre missatge de %s" % connexio.getpeername()[1])
   try:
       missatge = connexio.recv(MIDA_MISSATGE).decode("utf8")
       if len(missatge) == 0:
           return (RESULTA_ERROR, '')
       logging.info("Rebut missatge '%s'" % missatge)
       return (RESULTA_OK, missatge.strip())
   except socket.timeout:
       logging.warning("timeout en intentar rebre %s" % connexio.getpeername()[1])
       return (RESULTA_TIMEOUT, None)
   except OSError:
       logging.info("error en intentar rebre de %s" % connexio.getpeername()[1])
       return (RESULTA_ERROR, None)


def gestiona_participant(connexio, adressa, participants, finalitzacio):
    """ 
        Aquesta és la funció que gestiona les comunicacions que envia un
        participant a traves de la connexió fins que la marca de finalització
        s'estableix
    """
    logging.info("Iniciada gestió per nou participant %s" % str(adressa))

    # obté el nom del participant
    resultat, nom = rep(connexio)
    if resultat != RESULTA_OK:    # no s'ha aconseguit el nom i es finalitza l'execució
        logging.warning("No s'aconsegueix obtenir el nom del participant %s. Finalitzat." % str(adressa))
        logging.debug("XXX YYY (1) before closing unnamed participant %s" % str(adressa))
        connexio.close()
        return


    # envia missatge de benvinguda
    missatge = "Hola %s. Acabes d'entrar a la sala de xat de Fanjac. " \
               "De moment hi ha %s participants" % (nom, len(participants) + 1)
    resultat = envia(connexio, missatge)
    if resultat != RESULTA_OK:
        logging.info("No s'aconsegueix enviar la benvinguda al participant %s. Finalitzat." % str((adressa, nom)))
        logging.debug("XXX YYY (2) before closing participant %s" % str((adressa, nom)))
        connexio.close()

    # afegeix el nom del nou participant a la sala de participants
    participants[connexio] = (adressa, nom)
    logging.info("Vinculat el nou participant amb el seu nom %s" % str(participants[connexio]))

    # envia a la resta de participants la notificació del nou participant
    missatge = "S'ha afegit %s. Ara ja sou %s participants" % (nom, len(participants))
    broadcast(participants, missatge, [connexio])

    # comença a gestionar els missatges que generi el participant
    while not finalitzacio.isSet():
        resultat, missatge = rep(connexio)
        logging.info("Del participant %s rebut missatge [%s]: '%s'" % (str(participants[connexio]), resultat, missatge))
        if resultat == RESULTA_TIMEOUT:
            # s'ha exhaurit el temps, donem-li una altra oportunitat
            continue

        if resultat == RESULTA_ERROR:
            logging.warning("Perduda la connexió amb el participant %s" % str(participants[connexio]))
            missatge = "S'ha perdut la connexió %s" % connexio.getpeername()
            # envia notificació de finalització de participant
            broadcast(participants, missatge, [connexio])
            break

        if missatge == '{quit}':
            logging.info("Rebuda petició de finalització per part del participant %s" % str(participants[connexio]))
            missatge = "%s abandona la sala de xat" % participants[connexio][1]
            # envia notificació de finalització de participant
            broadcast(participants, missatge, [connexio])
            break

        logging.info("Rebut missatge per part de participant %s: %s" % (participants[connexio][1], missatge))
        reenviament = "%s: %s" % (participants[connexio][1], missatge)
        broadcast(participants, missatge, [connexio])

    if finalitzacio.isSet():
        missatge = "La sessió de xat ha estat tancada. Disculpa les molèsties."
        broadcast(participants, missatge)

    logging.info("Finalitza la gestió del participant %s" % str(participants[connexio]))
    # elimina el participant de la llista de participants

    logging.debug("XXX YYY (3) before closing participant %s" % str(participants[connexio]))
    connexio.close()
    participants.pop(connexio, None)


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
            llenca_fil_gestio_participant(nova_connexio, adressa, participants, finalitzacio)
            logging.info("Llençat fil d'execució per gestionar el nou participant %s" % str(adressa))
        except socket.timeout:
            # ha passat el temps màxim d'espera. Tornem a comprovar si encara cal continuar
            pass
        except OSError:
            missatge = "Ha caigut el servidor de xat. No es podran acceptar nous participants"
            logging.warning("Perduda connexió del servidor. Notificant participants")
            broadcast(participants, missatge)
            print(missatge)
            break

    # tanca el servidor
    logging.debug("XXX YYY (4) before closing the server")
    servidor.close()
    logging.info("Finalitzada la gestió de peticions")


def llenca_fil_gestio_de_peticions(ip, port, participants, finalitzacio):
    """ llença el fil d'execució que gestionarà les peticions de connexió dels participants del xat """
    threading.Thread(target=gestiona_peticions, args=(ip, port, participants, finalitzacio, )).start()


def llenca_fil_gestio_participant(connexio, adressa, participants, finalitzacio):
    """ llença el fil d'execució que gestionarà els missatges que enviï un parcicipant """
    threading.Thread(target=gestiona_participant, args=(connexio, adressa, participants, finalitzacio, )).start()


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
            print("\tfinalitza: finalitza el xat")
        elif 'quants'.startswith(comanda):
            print("El nombre de participants en aquest moment és %s" % len(participants))
        elif 'finalitza'.startswith(comanda):
            logging.info("Marcant l'esdeveniment de finalització per petició de la usuària")
            finalitzacio.set()
        else:
            print("Ho sento. No t'entenc. Escriu 'ajuda' per veure les opcions disponibles")

    print("Finalitzada la sessió de xat")

# configura el logging
logging.basicConfig(filename="%s.log" % sys.argv[0],level=logging.DEBUG, format="%(asctime)s %(levelname)s: %(message)s")
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
