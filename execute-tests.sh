#!/bin/bash

pushd $(dirname $0)

dco="docker compose -f docker-compose.test.yml"
$dco build
$dco run --rm tester pytest
exit_code=$?
$dco down
exit $exit_code
