#! /usr/bin/env python3

"""
    Implementació d'un servidor que:
    - accepta la connexió d'un client
    - rep el nom del client
    - li envia un missatge de salutació
    - finalitza

    No fa cap control d'errors
"""
import socket

host = 'localhost'
port = 8889

connexio = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
connexio.bind((host, port))
connexio.listen()
print("Esperant un client des de %s:%s" % (host, port))
participant, adressa = connexio.accept()
nom = participant.recv(1024).decode('utf8')
print("Rebut el nom %s" % nom)
contestacio = "Encantat de saludar-te, %s" % nom
participant.send(bytes(contestacio, "utf8"))
participant.close()
connexio.close()
