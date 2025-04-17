Installation
============

Package
-------

Install the **OpenAFS Library** and **Robot Framework** packages with
``pip``:

.. code-block:: console

   $ pip install robotframework-openafslibrary

Source code
-----------

Alternatively, the library may be installed from source code. This may be
helpful when developing new keywords.

.. code-block:: console

   $ git clone https://github.com/openafs-contrib/robotframework-openafslibrary
   $ cd robotframework-openafslibrary
   $ python configure.py
   $ make install-user  # or sudo make install

You will need to manually install ``robotframework`` when ``pip`` is not
installed.
