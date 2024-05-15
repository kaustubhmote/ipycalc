#!/bin/bash

IPYCALC_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
SRC=$IPYCALC_DIR/src
DOWNLOAD_KITTY=0
CONDA_ENV=0
CONDA_ENV_MODE="create"
CONDA_PRUNE=""
IPYCALC_EXEC=0

# Download the kitty terminal
if [ -d $SRC/kitty.app ]; then
    read -r -p "kitty.app already exists. Do you want to redownload the kitty terminal? [y/n] " response
        case $response in
            [yY]) DOWNLOAD_KITTY=1;;
            [nN]) DOWNLOAD_KITTY=0;;
            *) echo "did not understand the response. Choose y or n";;
        esac
else
    read -r -p "kitty.app does not exist. Do you want to download the kitty terminal? [y/n] " response
        case $response in
            [yY]) DOWNLOAD_KITTY=1;;
            [nN]) DOWNLOAD_KITTY=0;;
            *) echo "did not understand the response. Choose y or n";;
        esac
fi

if [ $DOWNLOAD_KITTY -eq 1 ]; then
   curl -L https://sw.kovidgoyal.net/kitty/installer.sh | sh /dev/stdin \
        dest=$SRC \
        launch=n
fi

# Create a conda environment
if [ -d $SRC/ipycalc_conda_env ]; then
    read -r -p "conda env already exists. Do you want to reinstall the env? [y/n] " response
        case $response in
            [yY]) CONDA_ENV=1; CONDA_ENV_MODE="update"; PRUNE="--prune";;
            [nN]) CONDA_ENV=0;;
            *) echo "did not understand the response. Choose y or n";;
        esac
else
    read -r -p "conda environment does not exist. Do you want create it now? [y/n] " response
        case $response in
            [yY]) CONDA_ENV=1; CONDA_ENV_MODE="create";;
            [nN]) CONDA_ENV=0;;
            *) echo "did not understand the response. Choose y or n";;
        esac
fi

if [ $CONDA_ENV -eq 1 ]; then
    conda env $CONDA_ENV_MODE --prefix $SRC/ipycalc_conda_env --file=$IPYCALC_DIR/ipycalc_conda.yml $PRUNE
fi


#----ipycalc executable file


if [ -d $SRC/ipycalc ]; then
    read -r -p "ipycalc executable exists. Do you want to reinstall it? [y/n] " response
        case $response in
            [yY]) IPYCALC_EXEC=1;;
            [nN]) IPYCALC_EXEC=0;;
            *) echo "did not understand the response. Choose y or n";;
        esac
else
    read -r -p "ipycalc executable does not. Do you want to make it now? [y/n] " response
        case $response in
            [yY]) IPYCALC_EXEC=1;;
            [nN]) IPYCALC_EXEC=0;;
            *) echo "did not understand the response. Choose y or n";;
        esac
fi

# write out ipycalc file
cat > $SRC/ipycalc << EOM
#!/bin/bash

SRC=$SRC
IPYCALC=\$SRC/ipycalc
IPY=\$SRC/ipycalc_conda_env/bin/ipython
KITTY=\$SRC/kitty.app/bin/kitty

\$KITTY --single-instance \\
       --config \$SRC/defaults/ipycalc_kitty.conf \\
       -d $SRC \\
       \$IPY -i --no-confirm-exit --no-banner -c  \\
       "exec(open(\"python_thread_import.py\").read(), globals())"
EOM

# give exec perimissions to ipycalc
chmod u+x $SRC/ipycalc