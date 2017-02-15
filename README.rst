.. image:: https://travis-ci.org/jonDel/state_machine.svg?branch=master
   :target: https://travis-ci.org/jonDel/state_machine
   :alt: Travis CI build status (Linux)

.. image:: https://img.shields.io/pypi/v/state_machine_db.svg
   :target: https://pypi.python.org/pypi/state_machine_db/
   :alt: Latest PyPI version

.. image:: https://readthedocs.org/projects/state-machine/badge/?version=master
   :target: http://state-machine.readthedocs.io/en/master/?badge=master
   :alt: Documentation Status

.. image:: https://coveralls.io/repos/github/jonDel/state_machine/badge.svg?branch=master
   :target: https://coveralls.io/github/jonDel/state_machine?branch=master

.. image:: https://landscape.io/github/jonDel/state_machine/master/landscape.svg?style=flat
    :target: https://landscape.io/github/jonDel/state_machine/master
    :alt: Code Health


state_machine
=============

**state_machine** provides the implementation of a state machine


Example
-------

.. code:: python

  >>> import logging
  >>> loggin.basicConfig()
  >>> from state_machine import StateMachine
  >>> st = StateMachine('/tmp/db.sqlite', 'first')
  >>> st.logger.setLevel('DEBUG')
  >>> st.start()
  >>> st.update_flag = True


Installation
------------

To install state_machine, simply run:

::

  $ pip install state_machine_db

state_machine is compatible with Python 2.6+

Documentation
-------------

https://state_machine.readthedocs.io

Source Code
-----------

Feel free to fork, evaluate and contribute to this project.

Source: https://github.com/jonDel/state_machine

License
-------

GPLv3 licensed.

