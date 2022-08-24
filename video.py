from os import popen
from time import sleep

def video_send():
    p = popen('''ffmpeg -f v4l2 \
                -i /dev/video0 \
                -f mpegts \
                -r 30 \
                -b:v 100k \
                -s 480x320 \
                -vcodec h264_v4l2m2m \
                -preset veryfast \
                -tune zerolatency \
                -bf 0 \
                udp://192.168.1.18:12345''')
    return p

def audio_send():
    p = popen('''ffmpeg -f alsa -ac 1 -i hw:HD3000 -b:a 32k -preset veryfast -tune zerolatency udp://192.168.1.18:12346''')
    return p

def video_listen():
    p = popen('''mpv --no-cache --untimed --no-demuxer-thread --video-sync=audio \
                 --vd-lavc-threads=1 udp://192.168.1.19:12345''')
    return p

def audio_listen():
    p = popen('''mpv --no-cache --untimed --no-demuxer-thread --video-sync=audio \
                 --vd-lavc-threads=1 udp://192.168.1.19:12346''')
    return p

if __name__ == '__main__':
    try:
        inp = input("send or listen").lower()[0]
        if inp == 's':
            p1 = video_send()
            p2 = audio_send()
        elif inp == 'l':
            p1 = video_listen()
            p2 = audio_listen()
        while 1:
            sleep(1000)
    finally:
        if inp == 's' or inp == 'l':
            p1.terminate()
            p2.terminate()
            p1.kill()
            p2.kill()
    