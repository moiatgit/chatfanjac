#!/ur/bin/env python3

"""
    Test del servidor de xat

    Hi ha dos participants

    p1 entra i envia nom
    p1 rep benvinguda

    p2 entra i envia nom
    p2 rep benvinguda
    p1 rep notificació entrada p2

    p1 envia salutació a p2
    p2 rep salutació de p1

    p1 envia {quit}
    p2 rep notificació sortida p1

    p2 envia {quit}

"""

import sys
import socket
import logging
import time
import os

MIDA_MISSATGE = 1024

logging.basicConfig(filename="client.py.log",
        level=logging.INFO, 
        format="%(asctime)s %(levelname)s: %(message)s")
logging.info("Arrenca el test 01")

# Obté la IP i el port de connexió amb el servidor
ip, port = sys.argv[1], int(sys.argv[2])

# p1 entra
connexio1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
connexio1.settimeout(2)
connexio1.connect((ip, port))
logging.info("Participant 1 connectat amb el servidor")

# p1 envia nom
nom = "participant1"
connexio1.send(bytes(nom, "utf8"))
logging.info("Participant1 enviat nom")

# p1 rep benvinguda
benvinguda = connexio1.recv(MIDA_MISSATGE).decode("utf8").strip()
logging.info("Participant1 rebut missatge '%s'" % benvinguda)
assert benvinguda == "Hola participant1. Acabes d'entrar a la sala de xat de Fanjac. De moment hi ha 1 participants"
logging.info("Participant1 Rebuda benvinguda")

# esperem perquè hi hagi prou temps per processar els missatges
logging.info("Espera perquè l'arribada del participant 2 no es barregi amb la del 1")
time.sleep(1)
logging.info("finalitzada l'espera")

# p2 entra
connexio2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
connexio2.settimeout(2)
connexio2.connect((ip, port))
logging.info("Participant 2 connectat amb el servidor")

# p2 envia nom
nom = "participant2"
connexio2.send(bytes(nom, "utf8"))
logging.info("Participant2 enviat nom")

# p2 rep benvinguda
benvinguda = connexio2.recv(MIDA_MISSATGE).decode("utf8").strip()
logging.info("Participant2 rebut missatge '%s'" % benvinguda)
assert benvinguda == "Hola participant2. Acabes d'entrar a la sala de xat de Fanjac. De moment hi ha 2 participants"
logging.info("Participant2 Rebuda benvinguda")

# p1 rep notificació entrada p2
logging.info("Participant1 intenta rebre notificació d'entrada de participant2")
missatge = connexio1.recv(MIDA_MISSATGE).decode("utf8").strip()
logging.info("Participant1 rebut missatge '%s'" % missatge)
assert missatge == "S'ha afegit participant2. Ara ja sou 2 participants"
logging.info("Participant1 rebut notificació nou participant")

# p1 envia salutació
logging.info("Participant1 envia salutació a participant2")
missatge = "Hola participant2, què tal?"
connexio1.send(bytes(missatge, "utf8"))
logging.info("Participant1 ha enviat salutació a participant2")

# p2 rep salutació
logging.info("Participant2 intenta rebre salutació")
missatge = connexio2.recv(MIDA_MISSATGE).decode("utf8").strip()
logging.info("Participant2 rebut missatge '%s'" % missatge)
assert missatge == 'Hola participant2, què tal?'
logging.info("Participant2 rep missatge de participant1")

# p1 envia {quit}
logging.info("Participant1 intenta enviar {quit}")
missatge = '{quit}'
connexio1.send(bytes(missatge, 'utf8'))
logging.info("Participant1 enviada %s" % missatge)

# p2 rep notificació abandonament p1
logging.info("Participant2 intenta rebre notificació d'abandonament de Participant1")
missatge = connexio2.recv(MIDA_MISSATGE).decode("utf8").strip()
logging.info("Participant2 rebut missatge '%s'" % missatge)
assert missatge == 'participant1 abandona la sala de xat'
logging.info("Participant2 rep notificació abandonament participant1")

# p2 envia {quit}
logging.info("Participant2 intenta enviar {quit}")
missatge = '{quit}'
connexio2.send(bytes(missatge, 'utf8'))
logging.info("Participant2 Enviada {quit}")


connexio1.close()
connexio2.close()
logging.info("Finalitzades les connexions")
print("OK")
