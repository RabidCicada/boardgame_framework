===================
BoardGame Framework
===================

A framework for implementing boardgames.

The idea is that the components here can be used with game specific modules that
import and use or simply "configure-together" game components with config files.

A BoardGame project framework by Kyle Stapp.

==========================
Get Developing!
==========================
Checkout the code:

.. code-block:: bash

   git clone http://github.com/RabidCicada/boardgame_framework

Install Dependencies:

.. code-block:: bash

    cd dev
    pip install requirements.txt

==========================
To Generate the Docs
==========================
Install Dev Dependencies then:

.. code-block:: bash

    cd docs
    make

To have pbr generate Changelog and AUTHORS automatically:

.. code-block:: bash

    python setup.py sdist

================
To Run the Tests
================

Quick and Dirty:

.. code-block:: bash

    cd src/
    python -m pytest ../tests
    or
    python -m pytest ../tests --log-cli-level DEBUG -s

The Right Way:

.. code-block:: bash

    tox

We use tox.  It builds virtual environments defined in tox.ini for different versions
of python, then builds the installable package, then installs it, then runs the tests.
It does this for all the versions you have defined and is suitable for continuous integration.

It is intentional that you cannot run a normal pytest command without PYTHONPATH
tomfoolery or calling pytest in the manner we show above for `Quick and Dirty`.
By not being importable it prevents a whole class of testing problems related to accidentally
getting your local dev code instead of what is installed by the package.

==========================
Frequently Asked Questions
==========================

1. Why this directory structure?
      https://blog.ionelmc.ro/2014/05/25/python-packaging/#the-structure

2. Why only python3?
      I didn't want to deal with compatibility.

3. Why Sphinx/restructured text instead of markdown?
      Ultimately because restructured text is more flexible and it is automatically usable
      by readthedocs.  Also, http://www.zverovich.net/2016/06/16/rst-vs-markdown.html.

4. Why Apache2 license?
      I want people to be able to do pretty much whatever they want.  But want to protect
      the project itself.
