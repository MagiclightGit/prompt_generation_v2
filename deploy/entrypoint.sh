#!/bin/bash

ACTION=$1

start_test_worker() {
    cd /workspace
    python /workspace/promptgpt_worker.py --yaml_config server_config_test.yaml --log-to-stdout
}

start_prod_worker() {
    cd /workspace
    python /workspace/promptgpt_worker.py --yaml_config server_config_prod.yaml --log-to-stdout
}

case $ACTION in
    "sleep" )
        echo "Sleep infinity"
        sleep infinity
        ;;
    "start_test" )
        echo "Start PromptGPT Worker on TEST"
        start_test_worker
        ;;
    "start_prod" )
        echo "Start PromptGPT Worker on PRDO"
        start_prod_worker
        ;;
    * )
        echo "unknown command"
        exit 1
        ;;
esac
