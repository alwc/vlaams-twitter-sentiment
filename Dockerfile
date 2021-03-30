# This Dockerfile creates the build image used by GitLab CI.
FROM continuumio/miniconda3:latest AS compile-image

# Allow cloning private repositories.
ARG GIT_TOKEN
RUN git config --global url."https://gitlab-ci-token:$GIT_TOKEN@gitlab.com/".insteadOf "ssh://git@gitlab.com/"

# Install compilers for certain pip requirements.
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

# Install conda environments. Minification inspired by [1].
# [1] https://jcrist.github.io/conda-docker-tips.html
COPY *.yml ./
RUN pip install conda-merge && \
    conda-merge environment.run.yml environment.dev.yml > environment.yml && \
    conda update --yes --name base conda && \
    conda env create --file environment.yml && \
    conda env create --file environment.run.yml && \
    conda clean --yes --all --force-pkgs-dirs --quiet && \
    cd /opt/conda/envs/sentiment-flanders-run-env/lib/python*/site-packages && du --max-depth=3 --threshold=5M -h | sort -h && cd - && \
    rm -rf /opt/conda/envs/*/lib/python*/site-packages/bokeh/server/static/ && \
    rm -rf /opt/conda/envs/*/lib/python*/site-packages/pydantic/*.cpython*.so && \
    find /opt/conda/ -follow -type d -name '__pycache__' -exec rm -r {} + && \
    find /opt/conda/ -follow -type d -name 'examples' -exec rm -r {} + && \
    find /opt/conda/ -follow -type d -name 'tests' -exec rm -r {} + && \
    find /opt/conda/ -follow -type f -name '*.a' -delete && \
    find /opt/conda/ -follow -type f -name '*.js.map' -delete && \
    find /opt/conda/ -follow -type f -name '*.pyc' -delete && \
    find /opt/conda/ -follow -type f -name '*.pyo' -delete && \
    cd /opt/conda/envs/sentiment-flanders-run-env/lib/python*/site-packages && du --max-depth=3 --threshold=5M -h | sort -h && cd -


# # 2. Create serverless image
FROM continuumio/miniconda3:latest AS build-image

# Install the Sentry CLI.
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/* && \
    curl -sL https://sentry.io/get-cli/ | bash

# Install the Serverless CLI.
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/* && \
    curl -o- -L https://slss.io/install | bash

# Activate conda environment.
ENV PYTHONDONTWRITEBYTECODE true
ENV PATH /opt/conda/envs/sentiment-flanders-env/bin:/root/.serverless/bin:$PATH
RUN echo "source activate sentiment-flanders-env" > ~/.bashrc

# Copy the conda environment from the compile-image.
COPY --from=compile-image /opt/conda/ /opt/conda/


# # 3. Create application image
FROM build-image AS app-image

# Automatically activate conda environment when opening a bash shell with `/bin/bash`.
WORKDIR /app/src/
ENV PYTHONPATH /app/src/:$PYTHONPATH

# Create Docker entrypoint.
RUN printf '#!/usr/bin/env bash\n\
    \n\
    set -e\n\
    \n\
    function run_update {\n\
    echo "Running batch-job to fetch and process tweets"\n\
    python -m batch.main\n\
    echo "Batch-job finished successfully!"\n\
    }\n\
    \n\
    function update_historical {\n\
    echo "Running batch-job over all previously fetched data"\n\
    python -m batch.update_historical\n\
    echo "Finished updating all historical data!"\n\
    }\n\
    \n\
    case "$1" in\n\
    update)\n\
    run_update\n\
    ;;\n\
    historical)\n\
    update_historical\n\
    ;;\n\
    bash)\n\
    /bin/bash "${@:2}"\n\
    ;;\n\
    esac\n\
    ' > /usr/local/bin/entrypoint.sh && chmod ugo+x /usr/local/bin/entrypoint.sh

ARG ENVIRONMENT
ENV ENVIRONMENT $ENVIRONMENT
ENV CI_COMMIT_REF_NAME $ENVIRONMENT

# Add source code to the `WORKDIR`
COPY src/sentiment_flanders sentiment_flanders
COPY src/sentiment_flanders/batch batch

# Configure application.
ARG PORT=8000
EXPOSE $PORT
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
