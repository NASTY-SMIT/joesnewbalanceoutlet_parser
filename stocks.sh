#!/bin/bash

# Путь к виртуальному окружению и проекту
PYTHON_ENV_PATH="/home/a/PycharmProjects/parsers/joesnewbalanceoutlet_parser/.venv"
SCRIPT_DIR="/home/a/PycharmProjects/parsers/joesnewbalanceoutlet_parser"

source ${PYTHON_ENV_PATH}/bin/activate

cd ${SCRIPT_DIR}

python3 main.py

deactivate