#!/bin/bash

ENV="test"
BUCKET_NAME="promptgpt-files"
KEY_PREFIX=""
PROJECT_NAME="prompt_generate"
PACKAGE_FOLDER="/home/ubuntu/yangel/prompt_generation"

UPSTREAM="${UPSTREAM:-"origin"}"

DATETIME=`date '+%Y%m%d%H%M'`
BUCKET_PREFIX="s3://${BUCKET_NAME}/${KEY_PREFIX}${ENV}"

cd ${PACKAGE_FOLDER}

git fetch ${UPSTREAM} --tags

PREV_COMMIT=$(cat .commit || echo '')
PREV_TAG=$(cat .tag || echo '')
echo "====== BACKUP LAST VERSION TO '${BUCKET_PREFIX}/codes/${DATETIME}_${PREV_TAG}_${PREV_COMMIT}.zip' ====== "
aws s3 cp ${BUCKET_PREFIX}/codes.zip ${BUCKET_PREFIX}/codes/${DATETIME}_${PREV_TAG}_${PREV_COMMIT}.zip

rm -f codes_*_latest.zip

GIT_COMMIT=`git rev-parse HEAD`
GIT_TAG=`git describe --tags`
echo $GIT_COMMIT > .commit
echo $GIT_TAG > .tag

git submodule update --init

zip codes_${ENV}_latest.zip  -r . \
    -x './**/__pycache__/*' \
    -x '**/.git/*' \
    -x '.git/*' \
    -x './log/*' \
    -x './logs/*' \
    -x './tmp/*' \
    -x 'fiction_folder/*' \
    -x'./__pycache__/*' \
    -x './_tmp/*' \
    -x './build.sh' \
    -x 'layer_prod.zip' \
    -x 'codes.zip' \
    -x 'start_service.sh' \
    -x 'update-*.sh' \
    -x 'start.sh' > /tmp/magic-update.log

aws s3 cp codes_${ENV}_latest.zip ${BUCKET_PREFIX}/codes.zip
aws s3 cp .commit ${BUCKET_PREFIX}/current-commit
aws s3 cp .tag ${BUCKET_PREFIX}/current-tag

echo "====== Uploaded, Print logs ======"

sleep 5
cat /tmp/magic-update.log
