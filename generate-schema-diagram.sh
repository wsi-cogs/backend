#!/bin/sh

set -eu

python <<EOF
from cogs.db.models import Base
import eralchemy
eralchemy.render_er(Base, "${1:-"schema-diagram.dot"}")
EOF
