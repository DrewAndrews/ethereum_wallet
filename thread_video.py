def record_video():
    start = time.monotonic()

    video = cv2.VideoCapture(0)
    frame_width = int(video.get(3))
    frame_height = int(video.get(4))

    out = cv2.VideoWriter("out.avi", cv2.VideoWriter_fourcc("M", "P", "P", "G"), 10, (frame_width, frame_height))

    while True:
        ret, frame = video.read()
        out.write(frame)
        end = time.monotonic()
        interval = int(end - start)
        if interval > 5:
            break
        ret, frame = video.read()
        out.write(frame)