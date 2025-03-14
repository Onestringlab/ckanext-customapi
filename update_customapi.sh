#!/bin/bash

COMMIT_MESSAGE="Initial Commit"
git add .
git commit -m "$COMMIT_MESSAGE"
git push -u origin master

sleep 30

# URL repository
REPO_URL="https://gitlab.data.go.id/sdi-2024/ckanext-custom-api.git"

# Nama container Docker
CONTAINER_NAME="ckan"

# Path ke direktori ekstensi di dalam container
EXT_PATH="/srv/app/ckanext-customapi"

# Pengecekan dan clone di dalam container, serta pembaruan
docker exec "$CONTAINER_NAME" bash -c "
    [ ! -d $EXT_PATH ] && git clone $REPO_URL $EXT_PATH
    cd $EXT_PATH && git pull && pip install -e .
"

# Restart container (opsional)
docker restart "$CONTAINER_NAME"
