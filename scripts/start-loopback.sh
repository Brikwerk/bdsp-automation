until ffmpeg -re -f v4l2 -i /dev/video0 -f v4l2 /dev/video2; do
    sleep 1
done