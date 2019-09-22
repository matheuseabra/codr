#!/bin/bash

echo "Cleaning pyc cache..."

cd ..

find . -name '*.pyc' -delete
