import os
import time
import cv2
import math
import mediapipe as mp
from mediapipe.tasks.python import vision, BaseOptions
from mediapipe.tasks.python.vision.core.vision_task_running_mode import VisionTaskRunningMode

from utils.paths import get_resource_dir

MODEL_PATH = os.path.join(get_resource_dir(), "models", "face_landmarker.task")


class BlinkDetector:
    def __init__(self, model_path=MODEL_PATH):
        options = vision.FaceLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=model_path),
            running_mode=VisionTaskRunningMode.VIDEO,
            num_faces=1,
            min_face_detection_confidence=0.5,
            min_face_presence_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self.face_landmarker = vision.FaceLandmarker.create_from_options(options)
        self._start_time = time.time()

        self.LEFT_EYE = [33, 160, 158, 133, 153, 144]
        self.RIGHT_EYE = [362, 385, 387, 263, 373, 380]
        self.MOUTH_TOP = 13
        self.MOUTH_BOTTOM = 14
        self.MOUTH_LEFT = 78
        self.MOUTH_RIGHT = 308
        self.FACE_LEFT = 234
        self.FACE_RIGHT = 454

        # Eyebrow Raise
        self.LEFT_EYEBROW_TOP = 105
        self.LEFT_EYE_TOP = 159
        self.RIGHT_EYEBROW_TOP = 334
        self.RIGHT_EYE_TOP = 386

        # Нормализация по масштабу лица
        self.FACE_TOP = 10
        self.FACE_BOTTOM = 152

    def calculate_ear(self, eye_points, landmarks, frame_width, frame_height):
        points = []
        for index in eye_points:
            x = int(landmarks[index].x * frame_width)
            y = int(landmarks[index].y * frame_height)
            points.append((x, y))

        v1 = math.dist(points[1], points[5])
        v2 = math.dist(points[2], points[4])
        h = math.dist(points[0], points[3])

        ear = (v1 + v2) / (2.0 * h) if h != 0 else 0
        return ear

    def calculate_mar(self, landmarks, frame_width, frame_height):
        top = int(landmarks[self.MOUTH_TOP].y * frame_height)
        bottom = int(landmarks[self.MOUTH_BOTTOM].y * frame_height)
        left = int(landmarks[self.MOUTH_LEFT].x * frame_width)
        right = int(landmarks[self.MOUTH_RIGHT].x * frame_width)

        v_dist = abs(top - bottom)
        h_dist = abs(left - right)

        return v_dist / h_dist if h_dist != 0 else 0

    def calculate_smile(self, landmarks, frame_width, frame_height):
        mouth_l = landmarks[self.MOUTH_LEFT]
        mouth_r = landmarks[self.MOUTH_RIGHT]
        face_l = landmarks[self.FACE_LEFT]
        face_r = landmarks[self.FACE_RIGHT]

        mouth_width = math.dist((mouth_l.x * frame_width, mouth_l.y * frame_height), (mouth_r.x * frame_width, mouth_r.y * frame_height))
        face_width = math.dist((face_l.x * frame_width, face_l.y * frame_height), (face_r.x * frame_width, face_r.y * frame_height))

        return mouth_width / face_width if face_width != 0 else 0

    def calculate_eyebrow_raise(self, landmarks, frame_width, frame_height):
        """Дистанция бровь-глаз, нормированная на высоту лица."""
        left_eyebrow = landmarks[self.LEFT_EYEBROW_TOP]
        left_eye = landmarks[self.LEFT_EYE_TOP]
        right_eyebrow = landmarks[self.RIGHT_EYEBROW_TOP]
        right_eye = landmarks[self.RIGHT_EYE_TOP]
        face_top = landmarks[self.FACE_TOP]
        face_bottom = landmarks[self.FACE_BOTTOM]

        left_dist = math.dist(
            (left_eyebrow.x * frame_width, left_eyebrow.y * frame_height),
            (left_eye.x * frame_width, left_eye.y * frame_height),
        )
        right_dist = math.dist(
            (right_eyebrow.x * frame_width, right_eyebrow.y * frame_height),
            (right_eye.x * frame_width, right_eye.y * frame_height),
        )
        face_height = math.dist(
            (face_top.x * frame_width, face_top.y * frame_height),
            (face_bottom.x * frame_width, face_bottom.y * frame_height),
        )

        avg_dist = (left_dist + right_dist) / 2.0
        return avg_dist / face_height if face_height != 0 else 0

    def process_frame(self, frame):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

        timestamp_ms = int((time.time() - self._start_time) * 1000)
        results = self.face_landmarker.detect_for_video(mp_image, timestamp_ms)

        features = {
            "ear": 0, "left_ear": 0, "right_ear": 0,
            "mar": 0, "smile": 0, "eyebrow_raise": 0,
            "landmarks": None,
        }

        if results.face_landmarks:
            face_landmarks = results.face_landmarks[0]

            left_ear = self.calculate_ear(self.LEFT_EYE, face_landmarks, frame.shape[1], frame.shape[0])
            right_ear = self.calculate_ear(self.RIGHT_EYE, face_landmarks, frame.shape[1], frame.shape[0])

            features["left_ear"] = left_ear
            features["right_ear"] = right_ear
            features["ear"] = (left_ear + right_ear) / 2.0
            features["mar"] = self.calculate_mar(face_landmarks, frame.shape[1], frame.shape[0])
            features["smile"] = self.calculate_smile(face_landmarks, frame.shape[1], frame.shape[0])
            features["eyebrow_raise"] = self.calculate_eyebrow_raise(face_landmarks, frame.shape[1], frame.shape[0])
            features["landmarks"] = face_landmarks

        return features
