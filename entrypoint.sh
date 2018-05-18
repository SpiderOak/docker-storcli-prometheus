#!/bin/bash
usage() {
    echo "usage: $0 <output_file> <interval>"
    exit 2
}
[ $# -eq 2 ] || usage
trap 'kill -TERM $child 2>/dev/null' SIGTERM
while true; do
    python /storcli.py > "$1" &
    child=$!; wait $child
    sleep "$2" &
    child=$!; wait $child
done
