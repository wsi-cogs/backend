# CoGS Web Application

[![Build Status](https://travis-ci.org/wtsi-cogs/webapp.svg?branch=master)](https://travis-ci.org/wtsi-cogs/webapp)
[![Test Coverage](https://codecov.io/gh/wtsi-cogs/webapp/branch/master/graph/badge.svg)](https://codecov.io/gh/wtsi-cogs/webapp)

## Interactively manipulating the database

It is possible to use a Python REPL to interact with the database:

```python
>>> from cogs import config
>>> from cogs.db.interface import Database
>>> c = config.load("config.yaml")
>>> db = Database(c["database"])
>>> # Now you can use `db.session` to manipulate the database.
>>> # It will probably be useful to import the models from `cogs.db.models`.
```
