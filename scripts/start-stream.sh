while :
do
    ffmpeg -f v4l2 -framerate 30 -video_size 720x480 -i /dev/video2 -f mpegts -codec:v mpeg1video -s 720x480 -b:v 1000k -bf 0 http://localhost:8080/ffmpeg
    sleep 1
done