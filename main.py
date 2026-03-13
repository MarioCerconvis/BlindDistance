import cv2
import numpy as np
from openni import openni2
import threading
import os
import time

from utils.audio_feedback import AudioFeedback
from utils.vision import ObstacleDetector
from data_recorder import DataRecorder

class AstraCamera:
    def __init__(self, project_path):
        # 0. Add DLL directory for Python 3.8+ on Windows
        if os.name == 'nt':
            os.environ['PATH'] = project_path + os.pathsep + os.path.join(project_path, 'OpenNI2') + os.pathsep + os.environ['PATH']
            if hasattr(os, 'add_dll_directory'):
                os.add_dll_directory(project_path)
                os.add_dll_directory(os.path.join(project_path, 'OpenNI2'))
            
        # 1. Initialize SDK and Device
        openni2.initialize(project_path)
        self.dev = openni2.Device.open_any()
        
        # 2. Create Streams
        self.depth_stream = self.dev.create_depth_stream()
        self.color_stream = self.dev.create_color_stream()
        
        # START STREAMS FIRST
        self.depth_stream.start()
        self.color_stream.start()

        # Read resolution from stream properties instead of hard-coding
        depth_vm = self.depth_stream.get_video_mode()
        color_vm = self.color_stream.get_video_mode()
        self.depth_h = depth_vm.resolutionY
        self.depth_w = depth_vm.resolutionX
        self.color_h = color_vm.resolutionY
        self.color_w = color_vm.resolutionX
        
        # 3. NOW set the registration mode (after streams are active)
        try:
            self.dev.set_image_registration_mode(openni2.IMAGE_REGISTRATION_DEPTH_TO_COLOR)
            self.dev.set_depth_color_sync_enabled(True)
            print("Image registration enabled.")
        except openni2.OpenNIError:
            print("Warning: Registration mode not supported or already active.")
        
        # Internal buffers, lock, and threads
        self.latest_depth = None
        self.latest_color = None
        self._lock = threading.Lock()
        self.running = True
        
        self.t_depth = threading.Thread(target=self._update_depth, daemon=True)
        self.t_color = threading.Thread(target=self._update_color, daemon=True)
        self.t_depth.start()
        self.t_color.start()

    def _update_depth(self):
        while self.running:
            try:
                frame = self.depth_stream.read_frame()
                data = frame.get_buffer_as_uint16()
                arr = np.frombuffer(data, dtype=np.uint16).reshape(self.depth_h, self.depth_w)
                with self._lock:
                    self.latest_depth = arr
            except Exception as e:
                print(f"Depth thread error: {e}")
                self.running = False
                break

    def _update_color(self):
        while self.running:
            try:
                frame = self.color_stream.read_frame()
                data = frame.get_buffer_as_uint8()
                rgb = np.frombuffer(data, dtype=np.uint8).reshape(self.color_h, self.color_w, 3)
                bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
                with self._lock:
                    self.latest_color = bgr
            except Exception as e:
                print(f"Color thread error: {e}")
                self.running = False
                break

    def get_frames(self):
        """ Returns copies of the latest frames if available, else (None, None) """
        with self._lock:
            if self.latest_depth is None or self.latest_color is None:
                return None, None
            return self.latest_depth.copy(), self.latest_color.copy()

    def stop(self):
        self.running = False
        self.depth_stream.stop()
        self.color_stream.stop()
        openni2.unload()

def draw_osd(img, label, recording, frame_count):
    """Draw on-screen display: label name, REC status, and frame count."""
    h, w = img.shape[:2]

    # Current label (top-left)
    label_text = f"[LABEL: {label}]"
    cv2.putText(img, label_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    # Recording status (top-right)
    if recording:
        rec_text = "  REC"
        rec_color = (0, 0, 255)  # red
    else:
        rec_text = "  PAUSED"
        rec_color = (180, 180, 180)  # gray
    text_size, _ = cv2.getTextSize(rec_text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
    cv2.putText(img, rec_text, (w - text_size[0] - 10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, rec_color, 2)

    # Frame count (bottom-left)
    count_text = f"Saved: {frame_count} frames"
    cv2.putText(img, count_text, (10, h - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 2)

    # Key hints (bottom-right)
    hint = "1-5:label  r:rec  q:quit"
    hint_size, _ = cv2.getTextSize(hint, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
    cv2.putText(img, hint, (w - hint_size[0] - 10, h - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (180, 180, 180), 1)

def main():
    project_path = os.path.dirname(os.path.abspath(__file__))
    
    # Initialize components
    cam = AstraCamera(project_path)
    audio = AudioFeedback()
    vision = ObstacleDetector()
    recorder = DataRecorder(base_dir='dataset', save_fps=2.0)

    # Recording state
    recording = False
    label_idx = 0  # default label: 'clear'
    
    # Grid Settings (dynamic based on camera, avoiding edges)
    grid_step_y = 20
    grid_step_x = 20
    # Provide a slight margin (e.g., 40px top, 20px sides/bottom)
    start_y, end_y = 40, cam.depth_h
    start_x, end_x = 20, cam.depth_w
    
    # Pre-calculate points for drawing to save loop time
    draw_points = [(y, x) for y in range(start_y, end_y, grid_step_y)
                          for x in range(start_x, end_x, grid_step_x)]

    # ── Floor-drop / void detection settings ─────────────────────────────────
    # The bottom third of the frame typically shows the floor ahead.
    # When the camera faces a staircase going DOWN or a hole, floor pixels either:
    #   (a) read much deeper than usual (stairs below reading 2000+ mm)
    #   (b) return 0 — sensor out-of-range for very deep drops / holes
    # We maintain a smoothed "floor baseline" from recent flat-ground readings
    # and warn when the floor region diverges significantly from it.
    floor_row_start = int(cam.depth_h * 0.67)   # bottom ~33% of frame = floor
    floor_void_multiplier = 1.5     # depth > baseline * 1.5  →  suspect void
    floor_void_ratio_thresh = 0.25  # >25% of floor pixels must look suspicious
    floor_ema_alpha = 0.05          # how fast the baseline adapts (0 = frozen)
    floor_baseline = None           # will be set on first valid frame
    # ─────────────────────────────────────────────────────────────────────────

    try:
        while True:
            depth_img, color_img = cam.get_frames()
            
            if depth_img is None or color_img is None:
                time.sleep(0.01) # Prevent maxing out CPU while waiting
                continue
            
            # 1. OPTIMIZED GRID EXTRACTION (NumPy Slicing)
            # Instantly get a 2D array of all grid depths instead of looping
            ai_grid_matrix = depth_img[start_y:end_y:grid_step_y, start_x:end_x:grid_step_x]
            
            # Flatten to 1D array if needed by external APIs
            grid_distance_flat = ai_grid_matrix.flatten().tolist()
            
            # Check for general proximity threats (any point > 0 and < 1000mm)
            # using fast boolean indexing
            valid_depths = ai_grid_matrix[ai_grid_matrix > 0]
            if valid_depths.size > 0:
                min_dist = np.min(valid_depths)
                if min_dist < 1000:
                    audio.beep(frequency=1000, duration_ms=100) # Warn user with sound

            # ── Floor-drop / void detection ───────────────────────────────────
            # Extract floor region (bottom third of depth frame)
            floor_region = depth_img[floor_row_start:, :]
            floor_valid = floor_region[(floor_region > 0) & (floor_region < 6000)]

            if floor_valid.size > 0:
                floor_current_median = float(np.median(floor_valid))

                # Initialise or update the exponential moving average baseline
                if floor_baseline is None:
                    floor_baseline = floor_current_median
                else:
                    floor_baseline = (floor_ema_alpha * floor_current_median
                                      + (1 - floor_ema_alpha) * floor_baseline)

                # Pixels that are MUCH deeper than the flat-floor baseline signal a void
                void_threshold = floor_baseline * floor_void_multiplier
                void_pixels = np.sum(floor_region > void_threshold)
                # Pixels with NO return (0) also indicate a void / hole out-of-range
                no_return_pixels = np.sum(floor_region == 0)
                suspicious_ratio = (void_pixels + no_return_pixels) / floor_region.size

                if suspicious_ratio > floor_void_ratio_thresh:
                    audio.speak("Warning! Drop ahead.", force=False)
            # ─────────────────────────────────────────────────────────────────

            # 2. RUN VISION AI 
            # YOLOv8 object detection on current frame
            annotated_img, threats = vision.process_frame(color_img, depth_img)
            
            # 3. CONTEXTUAL AUDIO WARNINGS
            for threat in threats:
                # If a specific recognized object is closer than 1 meter (or 0 meaning extremely close)
                dist_mm = threat['distance_mm']
                if dist_mm > 0 and dist_mm < 1000:
                    audio.speak(f"Warning! {threat['label']} at {dist_mm/1000:.1f} meters.")
                elif dist_mm == 0:
                    audio.speak(f"Warning! {threat['label']} very close.")
            
            # 4. DRAW RAW GRID WARNINGS (For debugging alongside YOLO)
            # It's faster to color the whole grid GREEN first, then selectively color RED
            for y, x in draw_points:
                dist = depth_img[y, x]
                color = (0, 0, 255) if (0 < dist < 1000) else (0, 255, 0)
                cv2.circle(annotated_img, (x, y), 2, color, -1)

            # 5. SAVE TRAINING DATA
            current_label = DataRecorder.LABELS[label_idx]
            if recording:
                recorder.save_frame(depth_img, annotated_img, grid_distance_flat, current_label)

            # 6. OSD OVERLAY
            draw_osd(annotated_img, current_label, recording,
                     recorder.get_frame_count(current_label))

            # 7. UI DISPLAY
            cv2.imshow("BlindDistance - AI Augmented View", annotated_img)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('r'):
                recording = not recording
                state = "STARTED" if recording else "PAUSED"
                print(f"Recording {state} — label: {DataRecorder.LABELS[label_idx]}")
            elif key in DataRecorder.LABEL_KEYS:
                label_idx = DataRecorder.LABEL_KEYS[key]
                print(f"Label changed to: {DataRecorder.LABELS[label_idx]}")
                
    finally: # Clean up hardware and threads gracefully
        print("Shutting down...")
        audio.stop()
        cam.stop()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
