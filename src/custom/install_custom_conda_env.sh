#!/bin/bash

IPYCALC_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
SRC=$IPYCALC_DIR/..
CONDA_ENV_MODE="update"
CONDA_PRUNE="--prune"

if [ -d $SRC/ipycalc_conda_env ]; then
    read -r -p "conda env already exists. Do you want to update the env? [y/n] " response
        case $response in
            [yY]) CONDA_ENV=1; CONDA_ENV_MODE="update"; PRUNE="--prune";;
            [nN]) CONDA_ENV=0;;
            *) echo "did not understand the response. Choose y or n";;
        esac
fi

if [ $CONDA_ENV -eq 1 ]; then
    conda env $CONDA_ENV_MODE --prefix $SRC/ipycalc_conda_env --file=$IPYCALC_DIR/ipycalc_custom_conda.yml $PRUNE
fi


