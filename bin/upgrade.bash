#!/bin/bash

echo "Upgrading migrations..."

flask db upgrade
