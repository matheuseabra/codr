#!/bin/bash

echo "Applying migration $1"

flask db migrate -m "$1"
