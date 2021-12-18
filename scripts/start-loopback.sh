if [[ $1 -eq 0 ]] ; then
    echo "Expected video resolution as argument (ex: 720x480)"
    echo "No argument supplied, exiting..."
    exit 1
fi

until ffmpeg -re -f v4l2 -video_size $1 -i /dev/video0 -f v4l2 -s $1 /dev/video2; do
    sleep 1
done