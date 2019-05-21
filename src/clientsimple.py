#! /usr/bin/env python3

"""
    Implementació d'un client que:
    - es connecta amb el servidor
    - envia un nom al servidor
    - rep un missatge del servidor
    - finalitza

    No fa cap control d'errors
"""
import socket

host = 'localhost'
port = 8889
nom = 'Gargamel'

connexio = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
connexio.connect((host, port))
connexio.send(bytes(nom, 'utf8'))
missatge = connexio.recv(1024).decode('utf8')
print("Rebut el missatge del servidor: %s" % missatge)
connexio.close()

