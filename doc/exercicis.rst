#################
Idees d'exercicis
#################

Algunes idees per treballar amb el xat de Fanjac

* Millora missatges d'informació

  A la versió inicial, al primer participant se li dóna un missatge de
  benvinguda molt pobre. Seria millor dir-li quelcom com "Ara per ara ets l'únic
  participant. A veure si venen més amiguets"

* No a tot

  Crear un client *bot* que cada cop que rebi un missatge respongui "no estic
  d'acord"

* No a tot selectiu

  És una versió del "no a tot" que només respon quan els missatges venen d'un
  determinat participant

  *pista*: es pot saber el nom del participant que envia el missatge, mirant el
  text entre corxets amb que comença el missatge rebut

  ::

        "[pep] hola".startswith("[pep]")

* Més control per l'administrador del servidor

  Afegir una nova comanda a la consola de l'administrador que permeti tancar la
  connexió a un dels participants pel nom, per exemple, perquè s'està portant
  malament.

* Noms sense repetir

  La versió inicial permet que dos participants es diguin igual. En cas que el
  nom ja estigui escollit, se li pot rebatejar amb el nom seguit d'un número
  seqüèncial. Ex. "pep", "pep1", "pep2"…

* Fer més segura la connexió

  Ara mateix, tothom que sàpiga el host i el port, podria connectar-se. I si
  volem fer un xat privat?

  Abans d'enviar el nom, els clients hauran d'enviar una contrassenya
  determinada. Si no encerten, es tanca la connexió

* El xat mou una tortuga remota

  Python ens ofereix la biblioteca ``turtle`` que, simplificant-ho molt, ens
  permet dibuixar amb *tortugues*

  Aquesta ampliació pretén gestionar una tortuga remota: client que quan rep un
  missatge que conté 'tortuga', executa la comanda que segueix. Les comandes
  poden ser, per començar:

  - pas
  - dreta
  - esquerra

* Tortuga multiusuari

  Ampliació de la gestió de tortuga, de manera que ara hi hagi una tortuga per
  cada participant.

