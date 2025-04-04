#!/usr/bin/env bash

declare -A Colors=(
    [Color_Off]='\033[0m'
    [Black]='\033[0;30m'
    [Red]='\033[0;31m'
    [Green]='\033[0;32m'
    [Yellow]='\033[0;33m'
    [Blue]='\033[0;34m'
    [Purple]='\033[0;35m'
    [Cyan]='\033[0;36m'
    [White]='\033[0;37m'
    [BBlack]='\033[1;30m'
    [BRed]='\033[1;31m'
    [BGreen]='\033[1;32m'
    [BYellow]='\033[1;33m'
    [BBlue]='\033[1;34m'
    [BPurple]='\033[1;35m'
    [BCyan]='\033[1;36m'
    [BWhite]='\033[1;37m'
    [UBlack]='\033[4;30m'
    [URed]='\033[4;31m'
    [UGreen]='\033[4;32m'
    [UYellow]='\033[4;33m'
    [UBlue]='\033[4;34m'
    [UPurple]='\033[4;35m'
    [UCyan]='\033[4;36m'
    [UWhite]='\033[4;37m'
)

set -euo pipefail