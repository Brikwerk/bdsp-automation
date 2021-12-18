#!/bin/bash
if ! command -v tmux &> /dev/null
then
    echo "tmux not found on your path. Please install tmux to continue."
    exit
fi

if ! command -v ffmpeg &> /dev/null
then
    echo "ffmpeg not found on your path. Please install ffmpeg to continue."
    exit
fi

if ! command -v python3 &> /dev/null
then
    echo "python3 not found on your path. Please install Python to continue."
    exit
fi

# Load v4l2loopback
sudo modprobe v4l2loopback

# Set streaming resolution
RESOLUTION="720x480"

# Setup tmux with the broadcasting servers
SESSION=switch_broadcast

tmux -2 new-session -d -s $SESSION

tmux new-window -t $SESSION:1 -n 'Switch Broadcast'
tmux split-window -h
tmux split-window -v

tmux select-pane -t 1
tmux send-keys './scripts/start-loopback.sh '"$RESOLUTION"'' C-m

tmux select-pane -t 0
tmux send-keys "python3 web_stream.py" C-m

tmux select-pane -t 2
tmux send-keys './scripts/start-stream.sh '"$RESOLUTION"'' C-m

tmux select-window -t $SESSION:1

tmux -2 attach-session -t $SESSION