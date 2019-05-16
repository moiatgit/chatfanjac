#!/ur/bin/env python3

"""
    Test del servidor de xat

    - connecta dos clients amb el servidor

    - envia els noms

    - rep els dos missatges de benvinguda

    - el primer rep confirmació entrada del segon

    - envia {quit} del primer

    - el segon rep confirmació de sortida del primer

    - envia {quit} del segon
"""

import sys
import socket
import logging
import time

MIDA_MISSATGE = 1024

logging.basicConfig(filename="client.py.log",
        level=logging.INFO, 
        format="%(asctime)s %(levelname)s: %(message)s")
logging.info("Arrenca el test 01")

# Obté la IP i el port de connexió amb el servidor
ip, port = sys.argv[1], int(sys.argv[2])

connexio1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
connexio1.settimeout(2)
connexio1.connect((ip, port))
logging.info("Participant 1 connectat amb el servidor")

nom = "participant1"
connexio1.send(bytes(nom, "utf8"))
logging.info("Participant1 enviat nom")

benvinguda = connexio1.recv(MIDA_MISSATGE).decode("utf8").strip()
logging.info("Participant1 rebut missatge '%s'" % benvinguda)
assert benvinguda == "Hola participant1. Acabes d'entrar a la sala de xat de Fanjac. De moment hi ha 1 participants"
logging.info("Participant1 Rebuda benvinguda")

connexio2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
connexio2.settimeout(2)
connexio2.connect((ip, port))
logging.info("Participant 2 connectat amb el servidor")

nom = "participant2"
connexio2.send(bytes(nom, "utf8"))
logging.info("Participant2 enviat nom")

benvinguda = connexio2.recv(MIDA_MISSATGE).decode("utf8").strip()
logging.info("Participant2 rebut missatge '%s'" % benvinguda)
assert benvinguda == "Hola participant2. Acabes d'entrar a la sala de xat de Fanjac. De moment hi ha 2 participants"
logging.info("Participant2 Rebuda benvinguda")

missatge = connexio1.recv(MIDA_MISSATGE).decode("utf8").strip()
logging.info("Participant1 rebut missatge '%s'" % missatge)
assert missatge == "S'ha afegit participant2. Ara ja sou 2 participants"
logging.info("Participant1 rebut notificació nou participant")

logging.info("Participant1 envia salutació a participant2")
missatge = "Hola participant2, què tal?"
connexio1.send(bytes(missatge, "utf8"))
logging.info("Participant1 ha enviat salutació a participant2")

logging.info("Participant2 rep el missatge del participant1")
missatge = "Hola participant2, què tal?"
connexio1.send(bytes(missatge, 'utf8'))
logging.info("Participant1 Enviat missatge")

time.sleep(1)

missatge = '{quit}'
connexio1.send(bytes(missatge, 'utf8'))
logging.info("Participant1 enviada %s" % missatge)

missatge = connexio2.recv(MIDA_MISSATGE).decode("utf8").strip()
logging.info("Participant2 rebut missatge '%s'" % missatge)
assert missatge == 'Hola participant2, què tal?'
logging.info("Participant2 rep missatge de participant1")

missatge = connexio2.recv(MIDA_MISSATGE).decode("utf8").strip()
logging.info("Participant2 rebut missatge '%s'" % missatge)
assert missatge == 'participant1 abandona la sala de xat'
logging.info("Participant2 rep notificació abandonament participant1")

missatge = '{quit}'
connexio2.send(bytes(missatge, 'utf8'))
logging.info("Participant2 Enviada {quit}")


connexio1.close()
connexio2.close()
logging.info("Finalitzades les connexions")
print("OK")
