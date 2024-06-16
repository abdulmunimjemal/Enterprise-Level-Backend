#!/usr/bin/env bash

DIR_PATH=$(realpath $(dirname "$0"))
source $DIR_PATH/colors.sh

IMAGE_NAME="auser/moodme"
IMAGE_TAG="latest"
CONTAINER_NAME="mmbackend_devcontainer-app"
FORCE_REBUILD_IMAGE=false
DOCKER_DIR=".devcontainer"
RUN_PRIVILEGED=false
VERBOSE="false"
PORTS=("8000:8000")
ADDITIONAL_ARGS=""
declare -a MOUNTS=("$(pwd):/workspace")

# docker_service_address=$(docker network inspect kind -f "{{(index .IPAM.Config 1).Subnet}}" | cut -d '.' -f1,2,3)
# my_ip=$(ipconfig getifaddr en0)
# api_server_address="${my_ip}"

docker_instance() {
    docker ps | grep "$CONTAINER_NAME" | awk '{print $1}'
}

build_image() {
    local image_id=$(docker images --filter=reference="$IMAGE_NAME" --format "{{.ID}}")
    if [[ "$FORCE_REBUILD_IMAGE" == "true" && -n "$image_id" ]]; then
        docker rmi "$image_id"
    fi
    local cmd=(docker build -f $DOCKER_DIR/Dockerfile.dev) 
    cmd+=(-t "$IMAGE_NAME:$IMAGE_TAG")
    [[ "$FORCE_REBUILD_IMAGE" == "true" ]] && cmd+=(--no-cache)
    cmd+=(".")

    if [[ "$VERBOSE" == "true" ]]; then
        printf "${Colors[BBlack]}%s" echo -e "${Colors[BBlack]}-------- Docker command --------${Colors[Color_Off]}"
        printf "${Colors[BBlack]}%s" echo -e "${Colors[Green]}${cmd[@]}${Colors[Color_Off]}"
    fi

    "${cmd[@]}"

    if [[ $? -eq 0 ]]; then
        printf "${Colors[BBlack]}${Colors[Green]}%s${Colors[Color_Off]}" "Image $IMAGE_NAME:$IMAGE_TAG built successfully"
    else
        printf "${Colors[BBlack]}${Colors[Red]}%s${Colors[Color_Off]}" "Failed to build image $IMAGE_NAME:$IMAGE_TAG"
        exit 1
    fi

    docker tag "$IMAGE_NAME:$IMAGE_TAG" "$IMAGE_NAME:latest"
}

start_container() {
    local docker_instance=$(docker_instance)
    echo "$docker_instance"
    if [[ -z "$docker_instance" ]]; then
        local cmd=(docker run --rm -it)
        [[ "$RUN_PRIVILEGED" == "true" ]] && cmd+=(--privileged)

        # Add volume mounts to the command
        for mount in "${MOUNTS[@]}"; do
            cmd+=(-v "$mount")
        done
        cmd+=($ADDITIONAL_ARGS)
        [[ -n "$CONTAINER_NAME" ]] && cmd+=(--name "$CONTAINER_NAME")

        cmd+=(--tmpfs /tmp --tmpfs /run)
        # --cpus="2.0" --memory="32g" --memory-swap=-1 --memory-reservation="16g"

        cmd+=(-d "$IMAGE_NAME" /sbin/init)

        if [[ "$VERBOSE" == "true" ]]; then
            echo_color "BBlack" "-------- Docker command --------"
            echo_color "Green" "${cmd[@]}"
        fi

        # Execute the command
        "${cmd[@]}"

        sleep 2
    fi
}

stop_container() {
    local docker_instance=$(docker_instance)
    if [[ -z "$docker_instance" ]]; then
        printf "${Colors[BRed]}No container found${Colors[Color_Off]}"
        exit 1
    fi
    docker stop ${docker_instance}
}

exec_instance() {
    local docker_instance=$(docker_instance)
    if [[ -z "$docker_instance" ]]; then
        printf "${Colors[BRed]}No container found${Colors[Color_Off]}"
        printf "${Colors[BGreen]}Starting container${Colors[Color_Off]}"
        start_container
        # exit 1
    fi
    docker exec -it ${docker_instance} /usr/bin/zsh
}

parse_opts() {
    local opt
    while getopts "n:p:v" opt; do
        case ${opt} in
            n ) CLUSTER_NAME=$OPTARG ;;
            p ) PORTS+=("$OPTARG") ;;
            v ) VERBOSE="true" ;;
            \? ) echo "Invalid option: $OPTARG" 1>&2; exit 1 ;;
        esac
    done
}

help() {
    echo -e "${Colors[BGreen]}Usage: $(basename "$0") [options] <command>${Colors[Color_Off]}
Options:
  -n  Name of the docker container (default: $CONTAINER_NAME)
  -p  Ports to map (default: $PORTS)
  -v  Verbose mode

Commands:
  ${Colors[Green]}build${Colors[Color_Off]}             Build the Docker image
  ${Colors[Green]}start${Colors[Color_Off]}             Start the Docker container
  ${Colors[Green]}stop${Colors[Color_Off]}              Stop the Docker container
  ${Colors[Green]}exec${Colors[Color_Off]}              Exec into the container
"
    exit 1
}

main() {
    parse_opts "$@"
    shift $((OPTIND - 1))
    if [ $# -eq 0 ]; then
        help
    fi
    case "$1" in
        build) build_image ;;
        start) start_container ;;
        stop) stop_container ;;
        exec) exec_instance ;;
        *) help ;;
    esac
}

main "$@"
