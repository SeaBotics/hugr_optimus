# README Monocamera
Specs:
0.3MP, 640x480, 30fps, 110 degree FOV, USB Direct, Manual Focus

Plan:
Centroid tracking (image coords) x,y 

This is made for testing and setting up the camera, the dedicated ros2 ws is a seperate folder.

# GStreamer and other dependencies
`sudo apt install v4l-utils`
`sudo apt install ros-jazzy-v4l2-camera`
`sudo apt install gstreamer1.0-tools gstreamer1.0-plugins-base \ gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly`

## Just stream
On RPi5:
`gst-launch-1.0 v4l2src device=/dev/video0   ! video/x-raw,format=YUY2,width=640,height=480,framerate=15/1   ! videoconvert ! x264enc tune=zerolatency speed-preset=ultrafast bitrate=1000 key-int-max=10   ! rtph264pay config-interval=1 pt=96 mtu=1200   ! udpsink host=fc94:2bc3:3275:e05c:1d1b:6bdf:6bbd:1e9b port=5000`

On Laptop:
`gst-launch-1.0 udpsrc address=:: port=5000   caps="application/x-rtp,media=video,encoding-name=H264,payload=96"   ! rtpjitterbuffer latency=50 ! rtph264depay ! h264parse ! avdec_h264   ! videoconvert ! autovideosink sync=false`

## ROS2 Topic
RPi5: `ros2 run v4l2_camera v4l2_camera_node --ros-args -p image_size:="[320,240]"`
Laptop: `ros2 run rqt_image_view rqt_image_view` <-Then choose the raw/compressed topic

# Using the test and calibration
1. Testing YOLO detection quality on your specific camera + lighting
2. Calibrating camera → world coords (if needed for arm reach)
3. Tuning centroid tracking (noise, jitter, confidence thresholds)
4. Validating the pipeline works end-to-end before you wire it to actual robot control

# Idea
The Video is compressed H.264 from rpi5 to laptop as a ros2 topic. That mean we can subscribe to this data, and use it. We apply YOLO on it, and make a generic interface with data to a new topic that is universal for other applications.

# Steps for D-R-T
1. We made test_node.py -> Just created a counter that subscribes and logs the frames we get
---
2. We made a yolo_test.py -> Now we Decompress with cv_bridge -> Feed to YOLO, do detecton -> Log detection (D)
**Note** Might be clever to use venv

I ran on only CPU (Laptop without GPU):
pip install --break-system-packages torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install --break-system-packages ultralytics opencv-python

If you have a GPU:
Download: `pip install --break-system-packages ultralytics opencv-python`

The yolo_test.py took the videostream, decompressed it, ran inference on it to detect (D) and  Recognize (R).
 Added cv2.imshow also, this allows us to see the feed to monitor and understand the D and R.
Look into reducing buffer size because we store 10 pcitures now, do inference and it build up.
---
3. Make a tracking software (T)
My idea is simple: 
a. Make a centroid be the lock in target, (x1+x2)/2 , (y1+y2)/2 this is our cx,cy the centroid, single point easier to focus on. 
Also reduces the noise if the bbox grows in x or y, the centroid is much less affected.
Cold perhaps implement an algoritm if the object seems bigger bigger we reduce physical movement since we lack the Z in the mono camera.
b. Have a filter or something "slow-react" or Lock on last known target, so when the bbox flickers we dont immediatly react, kind of like how a Low Pass filter on a P controller would work.
c. I belive the single track would suffice for following and mimicking, but multiple would be great for collison avoidance as we spawn multiple points to naviagte around.

4. The tracking software (T)
Start with a test, lock_test.py
Maybe play around with accepted confidence when tracking
Tracking: comparing last frame with new frame, callbacks only exists in the moment
Make it so we have a "memory" so new objects do not interfere with the tracking.
Make a smoother so the transition is good as mentioned in (3b)
Idea:
a. Nearest to last known lock -> We use the first and best object, note we have `results = self.model(frame, imgsz=320, classes=[n])` so n allows us to choose the correct one.
b. Reject wrong matches
c. Lost frame counter with timeout to reduce noise from flicker, etc
d. Smoothening for the frames, like a filter in (3b) or also a path tracer to see where the robot vision thinks it went.

This is the MVP, later perhaps som statistics and predictions or Kalman filters may be implemented.

See targeting_test.py
This tracks one bottle and locks on it, fails if bottle goes missing too long, but mvp for now easy use cases i think. We have a max_jump kind of as a protector, mvp for now.
---
5. Made it into a ros2 package
Data is sent -> We process -> Publish a standard interface with the x,y target, later may implement a custom intrface with probability but keeping it simple now.


# Note on Compositions and Intra-process communications
These are reserved rclcpp only (C++) not available in python code (rclpy). Made for image pipelines and reducing overhead.
