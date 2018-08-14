#!/usr/bin/env bash

# Start-up script that waits for Postgres to be ready
# Christopher Harrison <ch12@sanger.ac.uk>

set -eu

wait_for_postgres() {
  local -i max_attempts="$1"

  python -u <<-PYTHON
		import os
		from time import sleep
		
		from cogs import config
		from cogs.db.interface import Database
		
		config_file = os.getenv("COGS_CONFIG", "config.yaml")
		c = config.load(config_file)
		
		available = False
		attempts = 0
		while not available and attempts < ${max_attempts}:
		  try:
		    db = Database(c["database"])
		    available = True
		
		  except:
		    sleep_for = 2 ** attempts
		    print(f"Database is not ready yet! Will try again in {sleep_for} seconds...")
		    sleep(sleep_for)
		
		  attempts += 1
		
		if not available:
		  print("Could not connect to the database!")
		  exit(1)
		PYTHON
}

MAX_ATTEMPTS="${MAX_ATTEMPTS-5}"
wait_for_postgres "${MAX_ATTEMPTS}" >&2

exec python -"${1-}"m cogs.main
