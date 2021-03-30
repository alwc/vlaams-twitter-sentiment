#!/usr/bin/env bash
set -e

function log {
    local PURPLE='\033[0;35m'
    local NOCOLOR='\033[m'
    local BOLD='\033[1m'
    local NOBOLD='\033[0m'
    echo -e -n "${PURPLE}${BOLD}$1${NOBOLD}${NOCOLOR}" >&2
}

function install_vscode_extensions {
    export PATH="$PATH:/Applications/Visual Studio Code.app/Contents/Resources/app/bin"
    if [ -x "$(command -v code)" ]
    then
        log "Installing VS Code extensions...\\n"
        code --install-extension ms-python.python --force
        code --install-extension alexkrechik.cucumberautocomplete --force
        code --install-extension ms-azuretools.vscode-docker --force
        code --install-extension Atlassian.atlascode --force
        code --install-extension timonwong.shellcheck --force
        code --install-extension mauve.terraform --force
        log "Done!\\n"
    else
        log "VS Code CLI not found, skipping installation of extensions..."
    fi
}

function install_serverless {
    if ! [ -x "$(command -v serverless)" ]
    then
        log "Installing serverless...\\n"
        curl -o- -L https://slss.io/install | bash
        export PATH="$HOME/.serverless/bin:$PATH"
        log "Done!\\n"
    fi
}

function install_miniconda {
    if ! [ -x "$(command -v conda)" ]
    then
        log "Installing conda... "
        if [ "$(uname)" == "Darwin" ]; then local PLATFORM=MacOSX; else local PLATFORM=Linux; fi
        curl --silent https://repo.anaconda.com/miniconda/Miniconda3-latest-"$PLATFORM"-x86_64.sh --output /tmp/miniconda.sh
        bash /tmp/miniconda.sh -b -f > /dev/null
        export PATH="$HOME/miniconda3/bin:$PATH"
        conda init > /dev/null
        log "Done!\\n"
    fi
    rm /tmp/miniconda.sh 2> /dev/null || true
}

function update_conda {
    log "Updating conda... "
    conda update --name base --yes conda > /dev/null
    log "Done!\\n"
}

function create_conda_env {
    log "Creating conda environment sentiment-flanders-env...\\n\\n"
    local SCRIPT_PATH
    SCRIPT_PATH=$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)
    pip install --quiet conda-merge
    conda-merge environment.run.yml environment.dev.yml > environment.yml
    conda env create --prefix "$SCRIPT_PATH"/../.envs/sentiment-flanders-env --force
    conda config --append envs_dirs .envs 2> /dev/null
    rm environment.yml
    log "Done!\\n"
}

function configure_git {
    log "Installing pre-commit hooks...\\n"
    # shellcheck disable=SC1091
    source activate sentiment-flanders-env
    pre-commit install --hook-type pre-commit
    pre-commit install --hook-type prepare-commit-msg
    pre-commit install --hook-type pre-push
    log "Done!\\n"
    log "Enabling git push.followTags... "
    git config --local push.followTags true
    log "Done!\\n"
}

function list_tasks {
    log "Local environment ready! Remember to activate your conda environment with:\\n\\n"
    log "$ conda activate sentiment-flanders-env\\n\\n"
    log "After which you can list the available tasks with:\\n\\n"
    log "$ invoke --list\\n\\n"
    # shellcheck disable=SC1091
    source activate "sentiment-flanders-env"
    invoke --list
}

function run_command {
    local COMMAND=$1
    case $COMMAND in
    help|--help)
        cat << EOF
Usage: ./init.sh

Running this script will:

  - Install a set of recommended VS Code extensions.
  - Install serverless for the current user, if not already installed.
  - Install conda for the current user, if not already installed.
  - Update conda to the latest version.
  - Create the conda environment specified by the union of environment.run.yml and environment.dev.yml.
  - Install pre-commit hooks and configure git.
EOF
        ;;
    *)
        install_vscode_extensions
        install_serverless
        install_miniconda
        update_conda
        create_conda_env
        configure_git
        list_tasks
        ;;
    esac
}

run_command "$@"
