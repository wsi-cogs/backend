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

You can use a command like this to run the tests:

```console
$ python -m unittest discover -s test
```

## Testing time-based events

The development Docker image (use `Dockerfile.dev`) has [libfaketime][]
installed and configured, so you can modify the apparent flow of time
inside the container by writing to a file. Full documentation is
available in the libfaketime repository, but typically you would use it
like so:

```console
$ # Start up the container and add a rotation, then:
$ docker exec -ti name_of_the_container bash
# echo '+1d' > /etc/faketimerc
# # Now the application thinks one day has passed
# echo '+2d' > /etc/faketime
# # Now two days have passed, etc.
```

If there are events scheduled to happen between old and new times, you
will probably need to make some kind of HTTP request to the backend to
wake up the event loop and make the scheduler take notice of the new
time (due to caching inside libfaketime, you may need to wait up to 10
seconds before a refresh will have any effect). There is an API endpoint
enabled in development mode that shows the time inside the container,
`/api/util/time`, which you can use for this purpose.

libfaketime also supports altering the speed of the clock, so you can
run a full test at an increased rate without manual intervention:

```console
$ docker exec -ti name_of_the_container bash
# echo '+0 x144' > /etc/faketimerc
# # Ten minutes outside the container corresponds to one day inside the container
```

However, changing the multiplier at runtime [won't work how you
expect](https://github.com/wolfcw/libfaketime/issues/198).

If you use a bind-mount or volume to make the faketimerc available
outside the container, you must ensure that your editor does not use any
kind of "atomic save" where it writes to a different file and moves it
on top of the existing file, because this will break the bind-mount, and
until you restart the container, the contents of the files inside and
outside the container will no longer be synchronised.

[libfaketime]: https://github.com/wolfcw/libfaketime
