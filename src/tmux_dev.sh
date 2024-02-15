#!/bin/bash

session="pymap"

tmux new-session -ds $session

window=0

tmux rename-window -t $session:$window "Django"
tmux send-keys -t $session:$window "redis-server" C-m

tmux select-window -t $session:$window

tmux split-window -h
tmux send-keys "poetry run task serverDev" C-m

tmux split-window -v -t $session:$window.$window
tmux send-keys "poetry run task workerDev" C-m

tmux split-window -v -t $session:$window.2
tmux send-keys "poetry run task monitorDev" C-m

tmux attach -t $session
