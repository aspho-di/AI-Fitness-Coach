import cv2
import argparse
from pose_detector import PoseDetector
from angle_calculator import (
    calculate_angle_3d,
    calculate_back_angle,
    calculate_knee_deviation_3d,
    estimate_camera_angle,
    get_best_leg
)
from ui_renderer import UIRenderer
from calibration import Calibrator


BACK_ANGLE_LIMIT      = 35
KNEE_DEVIATION_LIMIT  = 0.15
CAMERA_WARNING_FRAMES = 90


def get_source():
    """Читает аргументы командной строки вместо input()."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=str, default='webcam', choices=['webcam', 'video'])
    parser.add_argument('--path',   type=str, default='')
    args = parser.parse_args()

    if args.source == 'video' and args.path:
        print(f"Opening video: {args.path}")
        return cv2.VideoCapture(args.path)
    else:
        print("Opening webcam...")
        return cv2.VideoCapture(0)


def main():
    detector = PoseDetector(detection_confidence=0.7, tracking_confidence=0.7)
    renderer = UIRenderer()

    cap = get_source()

    if not cap.isOpened():
        print("Error: source not found!")
        return

    # ── Калибровка ────────────────────────────────────────────────────────
    calibrator = Calibrator(detector)
    thresholds = calibrator.run(cap)

    SQUAT_UP_ANGLE   = thresholds["up_angle"]
    SQUAT_DOWN_ANGLE = thresholds["down_angle"]

    print(f"Thresholds — UP: >{SQUAT_UP_ANGLE} | DOWN: <{SQUAT_DOWN_ANGLE}")
    print("Press 'q' to quit.")

    counter              = 0
    stage                = None
    min_angle_reached    = 180
    camera_warning_timer = 0
    last_cam_deviation   = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Stream ended.")
            break

        results  = detector.process_frame(frame)
        detector.draw_skeleton(frame, results)

        leg       = get_best_leg(results)
        landmarks = detector.get_landmarks(results, frame.shape, leg=leg)

        feedback = "Stand in front of camera"
        color    = renderer.COLOR_YELLOW
        angle    = 0
        warnings = []

        if landmarks:
            shoulder = landmarks["shoulder"]
            hip      = landmarks["hip"]
            knee     = landmarks["knee"]
            ankle    = landmarks["ankle"]

            cam_position, cam_deviation = estimate_camera_angle({
                "left_hip_z":  landmarks["left_hip_z"],
                "right_hip_z": landmarks["right_hip_z"]
            })

            if cam_position == "diagonal":
                last_cam_deviation   = cam_deviation
                camera_warning_timer = CAMERA_WARNING_FRAMES

            angle      = calculate_angle_3d(landmarks["hip_3d"], landmarks["knee_3d"], landmarks["ankle_3d"])
            back_angle = calculate_back_angle(shoulder, hip)
            knee_dev   = calculate_knee_deviation_3d(landmarks["knee_3d"], landmarks["ankle_3d"], landmarks["hip_3d"])

            back_is_good = back_angle <= BACK_ANGLE_LIMIT

            if not back_is_good and stage == "DOWN":
                warnings.append("! Round back")
            if knee_dev < -KNEE_DEVIATION_LIMIT and stage == "DOWN":
                warnings.append("! Knees caving in")

            if stage == "DOWN":
                min_angle_reached = min(min_angle_reached, angle)

            if angle > SQUAT_UP_ANGLE:
                if stage == "DOWN":
                    if min_angle_reached <= SQUAT_DOWN_ANGLE:
                        counter += 1
                        feedback = "Great! Stand up!"
                        color    = renderer.COLOR_GREEN
                    else:
                        feedback = f"Not deep enough! Min: {int(min_angle_reached)} deg"
                        color    = renderer.COLOR_RED
                    min_angle_reached = 180
                else:
                    feedback = "Good! Go down!"
                    color    = renderer.COLOR_GREEN
                stage = "UP"

            elif angle < SQUAT_DOWN_ANGLE:
                stage    = "DOWN"
                feedback = "Great depth! Stand up!"
                color    = renderer.COLOR_GREEN
            else:
                if stage == "DOWN":
                    feedback = f"Lower! Need < {int(SQUAT_DOWN_ANGLE)} deg. Now: {int(angle)}"
                    color    = renderer.COLOR_RED
                else:
                    feedback = "Good! Go down!"
                    color    = renderer.COLOR_GREEN

            renderer.draw_joint_lines(frame, hip, knee, ankle, color)
            renderer.draw_angle(frame, knee, angle, color)
            renderer.draw_back_angle(frame, back_angle, back_is_good)

        renderer.draw_header(frame, counter, stage)
        renderer.draw_feedback(frame, feedback, color)
        renderer.draw_form_warnings(frame, warnings)

        if camera_warning_timer > 0:
            renderer.draw_camera_warning(frame, last_cam_deviation)
            camera_warning_timer -= 1

        cv2.imshow("AI Fitness Coach", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print(f"\nWorkout complete! You did {counter} squats.")


if __name__ == "__main__":
    main()