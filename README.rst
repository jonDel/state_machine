.. image:: https://travis-ci.org/jonDel/state_machine_db.svg?branch=master
   :target: https://travis-ci.org/jonDel/state_machine_db
   :alt: Travis CI build status (Linux)

.. image:: https://img.shields.io/pypi/v/state_machine_db.svg
   :target: https://pypi.python.org/pypi/state_machine_db/
   :alt: Latest PyPI version

.. image:: https://readthedocs.org/projects/state-machine-db/badge/?version=master
   :target: http://state-machine-db.readthedocs.io/en/master/?badge=master
   :alt: Documentation Status

.. image:: https://coveralls.io/repos/github/jonDel/state_machine_db/badge.svg?branch=master
   :target: https://coveralls.io/github/jonDel/state_machine_db?branch=master

.. image:: https://landscape.io/github/jonDel/state_machine_db/master/landscape.svg?style=flat
    :target: https://landscape.io/github/jonDel/state_machine_db/master
    :alt: Code Health


state_machine_db
================

**state_machine_db** provides the implementation of a recoverable (sqlite3) state machine


Example
-------

.. code:: python

  >>> import logging
  >>> loggin.basicConfig()
  >>> from state_machine_db import StateMachine
  >>> st = StateMachine('/tmp/db.sqlite', 'first')
  >>> st.logger.setLevel('DEBUG')
  >>> st.start()
  >>> st.update_flag = True


Installation
------------

To install state_machine, simply run:

::

  $ pip install state_machine_db

state_machine_db is compatible with Python 2.6+ and python 3

Documentation
-------------

https://state_machine_db.readthedocs.io

Source Code
-----------

Feel free to fork, evaluate and contribute to this project.

Source: https://github.com/jonDel/state_machine_db

License
-------

GPLv3 licensed.

