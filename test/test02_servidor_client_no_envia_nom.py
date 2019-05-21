#!/ur/bin/env python3

"""
    Test del servidor de xat

    Aquest test comprova que el servidor tanca la connexió amb el client
    després d'una estona sense enviar el nom

    - connecta amb el servidor

    - envia {quit}
"""

import sys
import socket
import logging
import time

MIDA_MISSATGE = 1024
MAXIM_ESPERA_CONNEXIO = 2

logging.basicConfig(filename="client.py.log",
        level=logging.INFO, 
        format="%(asctime)s %(levelname)s: %(message)s")
logging.info("Arrenca el test 02")

# Obté la IP i el port de connexió amb el servidor
ip, port = sys.argv[1], int(sys.argv[2])

connexio = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
connexio.settimeout(MAXIM_ESPERA_CONNEXIO)
connexio.connect((ip, port))
logging.info("Connectat amb el servidor")

logging.info("Start waiting")
time.sleep(5)   # espera molt de temps
logging.info("End waiting")

nom = "test"
connexio.send(bytes(nom, "utf8"))
logging.info("Enviat nom: no hauria de ser possible")


benvinguda = connexio.recv(MIDA_MISSATGE).decode("utf8").strip()
logging.info("rebut missatge '%s'" % benvinguda)
assert benvinguda == ''
logging.info("Rebuda benvinguda buida")

missatge = '{quit}'
try:
    connexio.send(bytes(missatge, 'utf8'))
    raise Exception("La connexió hauria d'estar trencada!")
except:
    pass

connexio.close()
logging.info("Finalitzada connexio")
print("OK")
