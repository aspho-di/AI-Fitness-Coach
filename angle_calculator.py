import numpy as np


def calculate_angle(a, b, c):
    # Computes the angle at point b between rays b→a and b→c (2D)
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)

    angle = np.degrees(
        np.arctan2(c[1] - b[1], c[0] - b[0]) -
        np.arctan2(a[1] - b[1], a[0] - b[0])
    )
    angle = abs(angle)
    if angle > 180:
        angle = 360 - angle
    return round(angle, 2)


def calculate_angle_3d(a, b, c):
    # Computes the angle at point b using x, y, z coords. Accurate at any camera angle
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)

    vec1 = a - b
    vec2 = c - b

    cos_angle = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
    cos_angle = np.clip(cos_angle, -1.0, 1.0)
    angle     = np.degrees(np.arccos(cos_angle))

    return round(angle, 2)


def calculate_back_angle(shoulder, hip):
    # Back lean angle relative to vertical. 0° = perfectly straight
    shoulder = np.array(shoulder)
    hip      = np.array(hip)

    vector   = shoulder - hip
    vertical = np.array([0, -1])

    cos_angle = np.dot(vector, vertical) / (np.linalg.norm(vector) * np.linalg.norm(vertical))
    cos_angle = np.clip(cos_angle, -1.0, 1.0)
    angle     = np.degrees(np.arccos(cos_angle))

    return round(angle, 2)


def calculate_back_angle_3d(shoulder_3d, hip_3d):
    # 3D back lean angle relative to vertical. Works at any camera angle. 0° = perfectly straight
    shoulder = np.array(shoulder_3d)
    hip      = np.array(hip_3d)

    vector   = shoulder - hip
    vertical = np.array([0, -1, 0])  # vertical in MediaPipe 3D space (Y points down)

    norm = np.linalg.norm(vector)
    if norm < 1e-6:
        return 0.0

    cos_angle = np.dot(vector, vertical) / norm
    cos_angle = np.clip(cos_angle, -1.0, 1.0)
    angle     = np.degrees(np.arccos(cos_angle))

    return round(angle, 2)


def calculate_knee_deviation_3d(knee_3d, ankle_3d, hip_3d):
    """
    Knee cave deviation using 3D coords. Works with diagonal cameras unlike 2D.

    Projects the knee onto the hip-ankle axis and measures lateral offset.
    Returns negative values for inward cave.
    """
    knee  = np.array(knee_3d)
    ankle = np.array(ankle_3d)
    hip   = np.array(hip_3d)

    # Vector from ankle to hip (leg axis)
    leg_axis = hip - ankle
    leg_axis_norm = np.linalg.norm(leg_axis)

    if leg_axis_norm < 1e-6:
        return 0.0

    # Project knee onto leg axis
    leg_unit   = leg_axis / leg_axis_norm
    knee_vec   = knee - ankle
    projection = np.dot(knee_vec, leg_unit) * leg_unit

    # Lateral deviation from leg axis
    deviation = knee_vec - projection
    deviation_magnitude = np.linalg.norm(deviation)

    # Sign based on X axis (left/right)
    sign = 1 if deviation[0] >= 0 else -1

    return round(sign * deviation_magnitude, 4)


def estimate_camera_angle(landmarks_3d):
    """
    Estimates camera angle from the Z-depth difference between hips.
    Returns ('side' | 'diagonal', deviation_degrees).
    """
    left_z  = landmarks_3d.get("left_hip_z", 0)
    right_z = landmarks_3d.get("right_hip_z", 0)

    z_diff       = abs(left_z - right_z)
    camera_angle = round(np.degrees(np.arctan(z_diff)) * 2, 1)
    position     = "diagonal" if z_diff > 0.1 else "side"

    return position, camera_angle


def get_best_leg(results, current_leg: str = "left", switch_threshold: float = 0.15) -> str:
    """
    Returns the leg with better joint visibility.
    switch_threshold prevents flickering when both legs are similarly visible.
    """
    if not results.pose_landmarks or len(results.pose_landmarks) == 0:
        return current_leg

    landmarks = results.pose_landmarks[0]

    left_visibility = (
        landmarks[23].visibility +
        landmarks[25].visibility +
        landmarks[27].visibility
    ) / 3

    right_visibility = (
        landmarks[24].visibility +
        landmarks[26].visibility +
        landmarks[28].visibility
    ) / 3

    if current_leg == "left":
        return "right" if right_visibility > left_visibility + switch_threshold else "left"
    else:
        return "left" if left_visibility > right_visibility + switch_threshold else "right"