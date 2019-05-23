###########
chat fanjac
###########

This project includes de code for an activity at `Fanjac's Barcelona club
<https://fanjacbarcelona.blogspot.com/>`_

The activity consists on presenting programming concepts to teenagers, most of
them previously unexposed to code. The code is mostly commented in Catalan to
ease comprehension.

It implements a chat room with a server able to accept multiple connexions.

Chat participants have a name and can receive and send messages in arbitrary
order.

Any suggestion will be highly appreciated.

To make it work
===============

This chat requires the execution of two programs ``server.py`` and
``client.py``.

You'll find them at folder ``src/``

The server must be launched before any client.

Server
======

Launch the server from a console by specifying the host and port it will be
listening

::

    $ python3 server.py host port

The server includes an interactive console. Type ``f`` to exit.

**Important**: when server finishes it's execution, it will notify all the
clients and they will finish their execution too.

Clients
=======

Launch the client from a console by specifying the host and port of the server

::

    $ python3 client.py host port

You can launch multiple clients

The client has an interactive console. Type ``{quit}`` to exit, anything else to
chat.

When a client enters and leaves the room, the rest of the participants get a
message with a notification.

Others
======

You can find other versions of clients and servers. They're there for conducting
the workshop. Maybe the most interesting one from the teenager's point of view
is ``clientturtle.py``. It is a client that processes the messages received from
the chat. When it interprets a message as a command, it moves a graphic pointer
(a ``turtle``)

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
