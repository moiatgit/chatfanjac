#!/usr/bin/env python3
"""Script for Tkinter GUI chat client."""
import socket
import sys
from threading import Thread

# Prompt que es mostrarà a la consola del client
PROMPT = '> '

# Mida màxima dels missatges a intercanviar entre el client i el servidor
MIDA_MISSATGE = 1024



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
        socket_servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket_servidor.connect((ip, port))
        return socket_servidor
    except ConnectionRefusedError:
        print("Error: no s'ha pogut connectar amb el servidor")
        sys.exit()


def gestiona_connexio():
    """ Gestiona la recepció de missatges per part de la connexió """
    while True:
        try:
            msg = rep()
            if not msg or msg == '{quit}':
                break
            print(msg)
            print(PROMPT, end='')
        except OSError:
            print("ERROR: S'ha trencat la connexió amb el servidor")
            break

def rep():
    """ obté un missatge del servidor i el retorna com a string """
    return socket_servidor.recv(MIDA_MISSATGE).decode("utf8").strip()

def send(missatge):  # event is passed by binders.
    """Handles sending of messages."""
    try:
        socket_servidor.send(bytes(missatge, "utf8"))
        return True
    except socket.error as e:
        print("S'ha perdut la connexió amb el servidor")
        print(e)
        return False


# Obté la IP i el port de connexió amb el servidor
ip, port, nom = obte_ip_port_i_nom(sys.argv)

socket_servidor = connecta_amb_servidor(ip, port)

receive_thread = Thread(target=gestiona_connexio)
receive_thread.start()

print("Connectat al servidor")
send(nom)
while receive_thread.is_alive():
    msg = input("%s" % PROMPT)
    correcte = send(msg)
    if msg == "{quit}" or not correcte:
        socket_servidor.close()
        break

print("Finalitzada la sessió")

