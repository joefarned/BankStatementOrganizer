#!/bin/bash

BASEDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

django-admin.py startproject $1 -v2 --name Makefile --extension py,conf --template $BASEDIR
cd $1 && make requirements && fab config && git init && make db
