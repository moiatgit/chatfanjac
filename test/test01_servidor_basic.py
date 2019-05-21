#!/ur/bin/env python3

"""
    Test del servidor de xat

    - connecta amb el servidor

    - envia el nom

    - rep el missatge de benvinguda

    - envia {quit}
"""

import sys
import socket
import logging

MIDA_MISSATGE = 1024

logging.basicConfig(filename="client.py.log",
        level=logging.INFO, 
        format="%(asctime)s %(levelname)s: %(message)s")
logging.info("Arrenca el test 01")

# Obté la IP i el port de connexió amb el servidor
ip, port = sys.argv[1], int(sys.argv[2])

connexio = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
connexio.settimeout(2)
connexio.connect((ip, port))
logging.info("Connectat amb el servidor")

nom = "test"
connexio.send(bytes(nom, "utf8"))
logging.info("Enviat nom")

benvinguda = connexio.recv(MIDA_MISSATGE).decode("utf8").strip()
logging.info("rebut missatge '%s'" % benvinguda)
assert benvinguda == "Hola test. Acabes d'entrar a la sala de xat de Fanjac. De moment hi ha 1 participants"
logging.info("Rebuda benvinguda")

missatge = '{quit}'
connexio.send(bytes(missatge, 'utf8'))
logging.info("Enviada {quit}")

connexio.close()
logging.info("Finalitzada connexio")
print("OK")
