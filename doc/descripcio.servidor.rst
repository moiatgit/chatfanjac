###########################################
Descripció de la implementació del servidor
###########################################

El servidor ha estat implementat de la següent manera:

- main:
  - crea el socket de servidor 
  - crear event finalització
  - crear llista de participants
  - crear llista de missatges pendents
  - llençar enviador de missatges
  - llençar acceptador de participants
  - processar les comandes interactives
  - quan es rep la comanda de finalització
    - envia un missatge a tots els participants actius avisant que es finalitza
    - marca event finalització

- enviador de missatges
  - rep les llistes de participants i de missatges, i l'esdeveniment de finalització
  - per cada missatge es comprova si el destinatari està actiu, si és així intenta enviar el missatge
  - si no es pot enviar el missatge, si el participant està encara a la llista, es marca com inactiu
  - quan no queden més missatges i s'ha marcat l'esdeveniment de finalització, finalitza execució

- acceptador de participants
  - rep les llistes de participants i de missatges, el socket de servidor i l'esdeveniment de finalització
  - per cada petició de nova connexió, llença un receptor del participant
  - quan hi ha un error amb el socket de servidor, el tanca i finalitza execució
  - quan s'ha marcat l'esdeveniment de finalització, tanca el socket de servidor i finalitza execució


- receptor de participant
  - rep el socket del participant, les llistes de participants i missatges
  - rep el nom del participant
  - envia la benvinguda al participant
  - envia notificació d'entrada de nou participant a la resta de participants
  - afegeix el nou participant a la llista de participants actius
  - escolta cada missatge que envïi el participant mentre el participant estigui actiu
  - per cada missatge que rep del participant
      - si rep el missatge '{quit}' del participant, 
        - marca el participant com a inactiu
        - notifica la resta de participants que ha marxat el participant
      - si rep un altre missatge, reenvia el missatge a la resta dels participants
  - quan el participant no està actiu
    - envia un missatge a la resta de participants notificant que el participant ha sortit
    - tanca la connexió amb el participant
    - elimina el participant de la llista de participants


Hi ha diferents casuístiques que potser requeririen un lock però que acaben resolent-se amb excepcions
Per exemple, si durant l'enviament d'un missatge, es rep {quit} del
destinatari, és possible que s'intenti enviar el missatge malgrat el
destinatari ja estaria desconnectat. Això generarà un error en l'enviament. L'enviador de missatges intentarà 
marcar el participant com a no actiu però aquest ja no es trobarà a la llista.

