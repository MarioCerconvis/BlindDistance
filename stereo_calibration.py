"""
stereo_calibration.py — Stereo Camera Calibration Tool for BlindDistance

Captures synchronized image pairs of a chessboard calibration pattern from
two USB webcams and computes:
  1. Intrinsic parameters (camera matrix + distortion) for each camera
  2. Extrinsic parameters (rotation + translation between cameras)
  3. Rectification maps for undistorting and aligning stereo pairs

Results are saved to an XML file that the main system loads at runtime.

Usage:
  python stereo_calibration.py                      # defaults
  python stereo_calibration.py --left 0 --right 2   # specify camera IDs
  python stereo_calibration.py --swap                # swap left/right

Controls:
  SPACE  — Capture a chessboard pair (must be visible in BOTH cameras)
  c      — Run calibration (requires >= 15 captured pairs)
  v      — Show rectification verification (after calibration)
  q      — Quit
"""

import argparse
import os
import sys
import time

import cv2
import numpy as np


# ─── Default Configuration ───────────────────────────────────────────────────

# Chessboard pattern: number of INNER CORNERS (not squares)
CHESSBOARD_SIZE = (8, 6)
SQUARE_SIZE_MM = 30.0  # physical size of each square in millimeters

# Camera resolution
FRAME_WIDTH = 640
FRAME_HEIGHT = 480

# Minimum number of image pairs required before calibration can proceed
MIN_PAIRS = 15

# Output file
OUTPUT_FILE = "stereo_calibration_data.xml"
IMAGES_DIR = "calibration_images"


# ─── Helper Functions ────────────────────────────────────────────────────────

def build_object_points(chessboard_size, square_size):
    """
    Build the 3D real-world coordinates of chessboard corners.
    The board is assumed to lie on the Z=0 plane.
    """
    objp = np.zeros((chessboard_size[0] * chessboard_size[1], 3), np.float32)
    objp[:, :2] = np.mgrid[
        0:chessboard_size[0],
        0:chessboard_size[1]
    ].T.reshape(-1, 2)
    objp *= square_size
    return objp


def open_camera(cam_id, width, height):
    """Open a camera with the specified resolution."""
    cap = cv2.VideoCapture(cam_id)
    if not cap.isOpened():
        print(f"[ERROR] Cannot open camera {cam_id}")
        sys.exit(1)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    # Allow auto-exposure to settle
    for _ in range(30):
        cap.read()
    return cap


def draw_status_bar(img, text, color=(0, 255, 0)):
    """Draw a status bar at the bottom of an image."""
    h, w = img.shape[:2]
    cv2.rectangle(img, (0, h - 35), (w, h), (0, 0, 0), -1)
    cv2.putText(img, text, (10, h - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)


def save_calibration(filename, image_size,
                     K1, D1, K2, D2, R, T, E, F,
                     R1, R2, P1, P2, Q,
                     map1x, map1y, map2x, map2y, rms_error):
    """Save all calibration data to an OpenCV XML/YAML FileStorage."""
    fs = cv2.FileStorage(filename, cv2.FILE_STORAGE_WRITE)
    fs.write("image_width", image_size[0])
    fs.write("image_height", image_size[1])
    fs.write("K1", K1)
    fs.write("D1", D1)
    fs.write("K2", K2)
    fs.write("D2", D2)
    fs.write("R", R)
    fs.write("T", T)
    fs.write("E", E)
    fs.write("F", F)
    fs.write("R1", R1)
    fs.write("R2", R2)
    fs.write("P1", P1)
    fs.write("P2", P2)
    fs.write("Q", Q)
    fs.write("map1x", map1x)
    fs.write("map1y", map1y)
    fs.write("map2x", map2x)
    fs.write("map2y", map2y)
    fs.write("rms_error", rms_error)
    fs.release()
    print(f"\n[OK] Calibration saved to: {filename}")
    print(f"     RMS Reprojection Error: {rms_error:.4f}")


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="BlindDistance Stereo Calibration Tool"
    )
    parser.add_argument("--left", type=int, default=0,
                        help="Left camera device ID (default: 0)")
    parser.add_argument("--right", type=int, default=1,
                        help="Right camera device ID (default: 1)")
    parser.add_argument("--swap", action="store_true",
                        help="Swap left and right cameras")
    parser.add_argument("--output", type=str, default=OUTPUT_FILE,
                        help=f"Output calibration file (default: {OUTPUT_FILE})")
    parser.add_argument("--rows", type=int, default=CHESSBOARD_SIZE[1],
                        help=f"Chessboard inner corner rows (default: {CHESSBOARD_SIZE[1]})")
    parser.add_argument("--cols", type=int, default=CHESSBOARD_SIZE[0],
                        help=f"Chessboard inner corner cols (default: {CHESSBOARD_SIZE[0]})")
    parser.add_argument("--square", type=float, default=SQUARE_SIZE_MM,
                        help=f"Square size in mm (default: {SQUARE_SIZE_MM})")
    args = parser.parse_args()

    left_id = args.right if args.swap else args.left
    right_id = args.left if args.swap else args.right
    chessboard_size = (args.cols, args.rows)
    square_size = args.square
    output_file = args.output

    print(f"╔══════════════════════════════════════════════════╗")
    print(f"║   BlindDistance — Stereo Calibration Tool        ║")
    print(f"╠══════════════════════════════════════════════════╣")
    print(f"║  Left camera:  {left_id:<5}                            ║")
    print(f"║  Right camera: {right_id:<5}                            ║")
    print(f"║  Chessboard:   {chessboard_size[0]}×{chessboard_size[1]} inner corners           ║")
    print(f"║  Square size:  {square_size:.0f} mm                           ║")
    print(f"║  Output file:  {output_file:<33} ║")
    print(f"╠══════════════════════════════════════════════════╣")
    print(f"║  SPACE = capture | c = calibrate | v = verify   ║")
    print(f"║  q = quit                                       ║")
    print(f"╚══════════════════════════════════════════════════╝")

    # Open cameras
    print("\n[INFO] Opening cameras...")
    cap_left = open_camera(left_id, FRAME_WIDTH, FRAME_HEIGHT)
    cap_right = open_camera(right_id, FRAME_WIDTH, FRAME_HEIGHT)
    print("[OK] Both cameras opened successfully.")

    # Prepare object points template
    objp = build_object_points(chessboard_size, square_size)

    # Storage for calibration data
    obj_points = []   # 3D points in real-world space
    img_points_L = [] # 2D points in left image
    img_points_R = [] # 2D points in right image

    # Calibration results (populated after 'c' is pressed)
    calibrated = False
    map1x = map1y = map2x = map2y = None

    # Create directory for saving calibration image pairs
    os.makedirs(IMAGES_DIR, exist_ok=True)

    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

    print("\n[INFO] Position the chessboard so it's visible in BOTH cameras.")
    print(f"[INFO] Press SPACE to capture. Need at least {MIN_PAIRS} pairs.\n")

    try:
        while True:
            ret_l, frame_l = cap_left.read()
            ret_r, frame_r = cap_right.read()

            if not ret_l or not ret_r:
                print("[WARN] Failed to read from one or both cameras.")
                continue

            display_l = frame_l.copy()
            display_r = frame_r.copy()

            # Convert to grayscale for corner detection
            gray_l = cv2.cvtColor(frame_l, cv2.COLOR_BGR2GRAY)
            gray_r = cv2.cvtColor(frame_r, cv2.COLOR_BGR2GRAY)

            # Status text
            n_pairs = len(obj_points)
            status = f"Pairs: {n_pairs}/{MIN_PAIRS}"
            if calibrated:
                status += " | CALIBRATED"
            status_color = (0, 255, 0) if n_pairs >= MIN_PAIRS else (0, 165, 255)
            draw_status_bar(display_l, f"LEFT  | {status}", status_color)
            draw_status_bar(display_r, f"RIGHT | {status}", status_color)

            # Combine side by side
            combined = np.hstack([display_l, display_r])
            cv2.imshow("Stereo Calibration", combined)

            key = cv2.waitKey(1) & 0xFF

            # ── SPACE: Capture pair ──────────────────────────────────────
            if key == ord(' '):
                found_l, corners_l = cv2.findChessboardCorners(
                    gray_l, chessboard_size, None
                )
                found_r, corners_r = cv2.findChessboardCorners(
                    gray_r, chessboard_size, None
                )

                if found_l and found_r:
                    # Refine corner positions to sub-pixel accuracy
                    corners_l = cv2.cornerSubPix(
                        gray_l, corners_l, (11, 11), (-1, -1), criteria
                    )
                    corners_r = cv2.cornerSubPix(
                        gray_r, corners_r, (11, 11), (-1, -1), criteria
                    )

                    obj_points.append(objp)
                    img_points_L.append(corners_l)
                    img_points_R.append(corners_r)

                    n_pairs = len(obj_points)

                    # Draw detected corners
                    vis_l = frame_l.copy()
                    vis_r = frame_r.copy()
                    cv2.drawChessboardCorners(vis_l, chessboard_size, corners_l, True)
                    cv2.drawChessboardCorners(vis_r, chessboard_size, corners_r, True)

                    # Save images for reference
                    cv2.imwrite(
                        os.path.join(IMAGES_DIR, f"pair_{n_pairs:03d}_left.png"), frame_l
                    )
                    cv2.imwrite(
                        os.path.join(IMAGES_DIR, f"pair_{n_pairs:03d}_right.png"), frame_r
                    )

                    # Show detected corners briefly
                    combined_vis = np.hstack([vis_l, vis_r])
                    draw_status_bar(
                        combined_vis,
                        f"CAPTURED pair #{n_pairs}!",
                        (0, 255, 0)
                    )
                    cv2.imshow("Stereo Calibration", combined_vis)
                    cv2.waitKey(500)

                    print(f"  [+] Pair #{n_pairs} captured successfully.")
                    if n_pairs >= MIN_PAIRS:
                        print(f"      Ready to calibrate! Press 'c'.")
                else:
                    # Show what was/wasn't found
                    msg_parts = []
                    if not found_l:
                        msg_parts.append("LEFT")
                    if not found_r:
                        msg_parts.append("RIGHT")
                    print(f"  [!] Chessboard NOT found in: {', '.join(msg_parts)}")

            # ── c: Run calibration ───────────────────────────────────────
            elif key == ord('c'):
                if n_pairs < MIN_PAIRS:
                    print(
                        f"  [!] Not enough pairs ({n_pairs}/{MIN_PAIRS}). "
                        f"Capture more with SPACE."
                    )
                    continue

                print(f"\n[INFO] Running stereo calibration with {n_pairs} pairs...")
                print("       This may take a minute...")

                image_size = (FRAME_WIDTH, FRAME_HEIGHT)

                # Step 1: Calibrate each camera individually
                print("  [1/4] Calibrating left camera...")
                rms_l, K1, D1, _, _ = cv2.calibrateCamera(
                    obj_points, img_points_L, image_size, None, None
                )
                print(f"         Left RMS: {rms_l:.4f}")

                print("  [2/4] Calibrating right camera...")
                rms_r, K2, D2, _, _ = cv2.calibrateCamera(
                    obj_points, img_points_R, image_size, None, None
                )
                print(f"         Right RMS: {rms_r:.4f}")

                # Step 2: Stereo calibration (extrinsic parameters)
                print("  [3/4] Running stereo calibration...")
                stereo_flags = (
                    cv2.CALIB_FIX_INTRINSIC  # use intrinsics from step 1
                )
                stereo_criteria = (
                    cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER,
                    100, 1e-5
                )
                rms_stereo, K1, D1, K2, D2, R, T, E, F = cv2.stereoCalibrate(
                    obj_points, img_points_L, img_points_R,
                    K1, D1, K2, D2, image_size,
                    criteria=stereo_criteria,
                    flags=stereo_flags
                )
                print(f"         Stereo RMS: {rms_stereo:.4f}")

                # Step 3: Compute rectification transforms
                print("  [4/4] Computing rectification maps...")
                R1, R2, P1, P2, Q, roi1, roi2 = cv2.stereoRectify(
                    K1, D1, K2, D2, image_size, R, T,
                    alpha=0  # crop to valid pixels only
                )

                # Precompute undistort+rectify maps for fast remapping
                map1x, map1y = cv2.initUndistortRectifyMap(
                    K1, D1, R1, P1, image_size, cv2.CV_32FC1
                )
                map2x, map2y = cv2.initUndistortRectifyMap(
                    K2, D2, R2, P2, image_size, cv2.CV_32FC1
                )

                # Save to file
                save_calibration(
                    output_file, image_size,
                    K1, D1, K2, D2, R, T, E, F,
                    R1, R2, P1, P2, Q,
                    map1x, map1y, map2x, map2y,
                    rms_stereo
                )

                calibrated = True
                print("\n[OK] Calibration complete! Press 'v' to verify.")

            # ── v: Verify rectification ──────────────────────────────────
            elif key == ord('v'):
                if not calibrated:
                    print("  [!] Calibrate first by pressing 'c'.")
                    continue

                ret_l, frame_l = cap_left.read()
                ret_r, frame_r = cap_right.read()
                if not ret_l or not ret_r:
                    continue

                # Apply rectification
                rect_l = cv2.remap(frame_l, map1x, map1y, cv2.INTER_LINEAR)
                rect_r = cv2.remap(frame_r, map2x, map2y, cv2.INTER_LINEAR)

                # Draw horizontal epipolar lines
                combined_rect = np.hstack([rect_l, rect_r])
                h = combined_rect.shape[0]
                for y in range(0, h, 30):
                    cv2.line(
                        combined_rect,
                        (0, y),
                        (combined_rect.shape[1], y),
                        (0, 255, 0), 1
                    )

                draw_status_bar(
                    combined_rect,
                    "RECTIFICATION VERIFICATION — Lines should align horizontally | "
                    "Press any key to close",
                    (0, 255, 255)
                )
                cv2.imshow("Rectification Verification", combined_rect)
                cv2.waitKey(0)
                cv2.destroyWindow("Rectification Verification")

            # ── q: Quit ──────────────────────────────────────────────────
            elif key == ord('q'):
                break

    finally:
        cap_left.release()
        cap_right.release()
        cv2.destroyAllWindows()
        print("\n[INFO] Calibration tool closed.")


if __name__ == "__main__":
    main()
