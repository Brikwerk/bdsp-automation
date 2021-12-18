if [[ $1 -eq 0 ]] ; then
    echo "Expected video resolution as argument (ex: 720x480)"
    echo "No argument supplied, exiting..."
    exit 1
fi

while :
do
    ffmpeg -f v4l2 -framerate 30 -video_size $1 -i /dev/video2 -f mpegts -codec:v mpeg1video -s $1 -b:v 1000k -bf 0 http://localhost:8080/ffmpeg
    sleep 1
done