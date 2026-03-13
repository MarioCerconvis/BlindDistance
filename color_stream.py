import cv2
import numpy as np
from openni import openni2

# 1. Initialize using your project path
project_path = r"C:\Users\LAOB\Desktop\Mário\BlindDistance"
openni2.initialize(project_path)

# 2. Open the device
dev = openni2.Device.open_any()

# 3. Create and start ONLY the Color Stream
color_stream = dev.create_color_stream()
color_stream.start()

print("Streaming Color... Press 'q' to stop.")

try:
    while True:
        # Grab a color frame
        frame = color_stream.read_frame()
        
        # OpenNI provides raw bytes (RGB), so we use uint8
        frame_data = frame.get_buffer_as_uint8()
        
        # Reshape to a standard 640x480 RGB image (3 channels)
        img_rgb = np.frombuffer(frame_data, dtype=np.uint8).reshape(480, 640, 3)
        
        # IMPORTANT: OpenCV uses BGR format, but OpenNI gives RGB.
        # We must swap the channels so the colors look real.
        img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
        
        # Show the image
        cv2.imshow("Astra Mini Pro - Color View", img_bgr)

        # Exit if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
finally:
    # Cleanup
    color_stream.stop()
    openni2.unload()
    cv2.destroyAllWindows()