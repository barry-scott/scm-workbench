#!/bin/bash
make -f linux.mak PYTHON=${PYTHON:?missing python def} clean build
