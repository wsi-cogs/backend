# CoGS Web Application

[![Build Status](https://travis-ci.org/wtsi-cogs/webapp.svg?branch=master)](https://travis-ci.org/wtsi-cogs/webapp)
[![Test Coverage](https://codecov.io/gh/wtsi-cogs/webapp/branch/master/graph/badge.svg)](https://codecov.io/gh/wtsi-cogs/webapp)

## Interactively manipulating the database

It is possible to use a Python REPL to interact with the database:

```python
>>> from cogs import config
>>> from cogs.db.interface import Database
>>> from cogs.db.models import *
>>> c = config.load("config.yaml")
>>> db = Database(c["database"])
>>> # Now you can use `db.session` to e.g. list all users:
>>> db.session.query(User).all()
```

## Running the tests

You can use the following command to run the tests:

```console
$ python setup.py test
```

or, if you prefer, you can run unittest directly, in which case you will
need to install the dependencies by hand (see the `tests` extra):

```console
$ python -m unittest discover test
```

<!-- vim: set tw=72: -->
