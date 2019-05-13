#!/ur/bin/env python3
"""
    Implementació del servidor de xat de Fanjac
"""

import logging
import threading
import time

logging.basicConfig(level=logging.DEBUG, format='(%(threadName)s) %(message)s')

def gestiona_connexions(finalitza):
    """ Aquesta funció se n'encarrega de gestionar connexions mentre 
        finaltza no estigui marcat
        finalitza és un threading.Event
    """
    logging.debug('Comença')
    intents = 0
    while not finalitza.isSet():
        logging.debug('Esperant intent %s' % intents)
        time.sleep(1)
        intents += 1
        if intents > 4:
            logging.debug('Cansat desperar. Marco jo el final')
            finalitza.set()
            logging.debug('Marcat finalitzar')

    logging.debug('Finalitzant')

logging.debug('Arrencant')
finalitza = threading.Event()
t = threading.Thread(name='gestiona_connexions', target=gestiona_connexions, args=(finalitza,))
t.start()

for t in threading.enumerate():
    logging.debug('\tthread disponible %s', t.getName())
logging.debug('Esperant abans de marcar finalitzar')
time.sleep(6)
logging.debug('Anem a marcar finalitzar')
finalitza.set()
logging.debug('Marcat finalitzar')
for t in threading.enumerate():
    logging.debug('\tthread disponible %s', t.getName())
