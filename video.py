from os import popen
from time import sleep
import os

def video_send():
    p = popen(f'''ffmpeg -f v4l2 \
                -i /dev/video0 \
                -f mpegts \
                -r 30 \
                -b:v 1M \
                -s 960x640 \
                -vcodec h264_v4l2m2m \
                -preset veryfast \
                -tune zerolatency \
                -bf 0 \
                udp://{os.getenv('FORWARDING_SERVER')}:25567''')
    return p

def audio_send():
    p = popen(f'''ffmpeg -f alsa -ac 1 -i hw:HD3000 -acodec mp2 -ab 32k -f wav udp://{os.getenv('FORWARDING_SERVER')}:25568''')
    return p

def video_listen():
    p = popen(f'''mpv --no-cache --untimed --no-demuxer-thread --video-sync=audio \
                 --vd-lavc-threads=1 --profile=low-latency udp://0.0.0.0:25567''')
    return p

def audio_listen():
    p = popen(f'''mpv --no-cache --untimed --no-demuxer-thread --video-sync=audio \
                 --vd-lavc-threads=1 --profile=low-latency udp://0.0.0.0:25568''')
    return p

if __name__ == '__main__':
    try:
        inp = input("send or listen? ").lower()[0]
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
            try:
                p1.terminate()
                p2.terminate()
            except:
                pass
            try:
                p1.kill()
                p2.kill()
            except:
                pass
    