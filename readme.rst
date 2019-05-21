#########
fanjachat
#########

This project is an activity for Fanjac's club

It implements a chat room with a server able to accept multiple connexions.

Participants have a name and can receive and send messages in arbitrary order.


To make it work
===============

This chat requires the execution of two programs ``server.py`` and
``client.py``.

You'll find them at folder ``src/``

The server must be launched before any client.

Server
======

Launch the server from a console by specifying the ip and port it will be
listening

::

    $ python3 server.py ip port

Finish server execution with ctrl-c

**Important**: when server finishes it's execution, it will notify all the
clients and they will finish their execution too.

Clients
=======

Launch the client from a console by specifying the ip and port of the server

::

    $ python3 client ip port

You can launch multiple clients

To leave the room and finish, press ctrl-c.

When a client enters and leaves the room, the rest of the participants get a
message with a notification.



References
==========

Inspired by the following sources:

- https://www.geeksforgeeks.org/simple-chat-room-using-python/

- https://medium.com/swlh/lets-write-a-chat-app-in-python-f6783a9ac170


License
=======

You can do whatever you want with the contents of this project under the terms
of the GNU General Public License as published by the Free Software Foundation,
either version 3 of the License, or any later version (your choice)
