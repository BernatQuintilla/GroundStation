import threading
import cv2
import mediapipe as mp
from Dron import Dron
import time

global dron
global cap


def initialize ():
    global pose
    global mp_drawing
    global mp_drawing_styles
    global mp_pose

    mp_drawing = mp.solutions.drawing_utils
    mp_drawing_styles = mp.solutions.drawing_styles
    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose(
            static_image_mode=True,
            model_complexity=2,
            enable_segmentation=True,
            min_detection_confidence=0.5)


def prepareBody(image):
    global pose
    global mp_drawing
    global mp_drawing_styles
    global mp_pose


    image.flags.writeable = False
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    # aqui pedimos la identificacion de los puntos clave
    results = pose.process(image)
    image.flags.writeable = True

    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    # marcamos en la imagen los puntos clave
    mp_drawing.draw_landmarks(
        image,
        results.pose_landmarks,
        mp_pose.POSE_CONNECTIONS,
        landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style())
    bodyLandmarks = []
    # preparamos la lista con los puntos clave
    if results.pose_landmarks:
        for landmark in results.pose_landmarks.landmark:
            bodyLandmarks.append([landmark.x, landmark.y])
    return bodyLandmarks, image

# En esta función determinamos la pose comparando las posiciones relativas de los puntos clave
# Aquí es donde se pueden añadir nuevas poses
def detectPose (bodyLandmarks):
    # pose 1
    if  bodyLandmarks[14][0] < bodyLandmarks[12][0] and \
        bodyLandmarks[16][0] < bodyLandmarks[14][0] and \
        bodyLandmarks[16][1] < bodyLandmarks[14][1] and \
        bodyLandmarks[14][1] < bodyLandmarks[12][1] and \
        bodyLandmarks[13][0] > bodyLandmarks[11][0] and \
        bodyLandmarks[15][0] > bodyLandmarks[13][0] and \
        bodyLandmarks[15][1] < bodyLandmarks[13][1] and \
        bodyLandmarks[13][1] < bodyLandmarks[11][1]:
        return 1
    # pose 2
    elif  bodyLandmarks[14][0] < bodyLandmarks[12][0] and \
        bodyLandmarks[16][0] > bodyLandmarks[14][0] and \
        bodyLandmarks[16][1] < bodyLandmarks[14][1] and \
        bodyLandmarks[14][1] < bodyLandmarks[12][1] and \
        bodyLandmarks[13][0] > bodyLandmarks[11][0] and \
        bodyLandmarks[15][0] > bodyLandmarks[13][0] and \
        bodyLandmarks[15][1] < bodyLandmarks[13][1] and \
        bodyLandmarks[13][1] < bodyLandmarks[11][1]:
        return 2
    # pose 3
    elif bodyLandmarks[14][0] < bodyLandmarks[12][0] and \
            bodyLandmarks[16][0] > bodyLandmarks[14][0] and \
            bodyLandmarks[16][1] < bodyLandmarks[14][1] and \
            bodyLandmarks[14][1] < bodyLandmarks[12][1] and \
            bodyLandmarks[13][0] > bodyLandmarks[11][0] and \
            bodyLandmarks[15][0] < bodyLandmarks[13][0] and \
            bodyLandmarks[15][1] < bodyLandmarks[13][1] and \
            bodyLandmarks[13][1] < bodyLandmarks[11][1]:
        return 3
    # pose 4
    if bodyLandmarks[14][0] < bodyLandmarks[12][0] and \
            bodyLandmarks[16][0] < bodyLandmarks[14][0] and \
            bodyLandmarks[14][1] < bodyLandmarks[12][1] and \
            bodyLandmarks[16][1] < bodyLandmarks[14][1] and \
            bodyLandmarks[11][0] < bodyLandmarks[13][0] and \
            bodyLandmarks[13][0] < bodyLandmarks[15][0] and \
            bodyLandmarks[13][1] > bodyLandmarks[11][1] and \
            bodyLandmarks[15][1] > bodyLandmarks[13][1]:
        return 4
    # pose 5
    elif bodyLandmarks[12][0] > bodyLandmarks[14][0] and \
            bodyLandmarks[14][1] < bodyLandmarks[12][1] and \
            bodyLandmarks[16][1] < bodyLandmarks[14][1] and \
            bodyLandmarks[16][0] > bodyLandmarks[12][0] and \
            bodyLandmarks[16][0] < bodyLandmarks[11][0] and \
            bodyLandmarks[11][0] < bodyLandmarks[13][0] and \
            bodyLandmarks[13][1] > bodyLandmarks[11][1] and \
            bodyLandmarks[15][0] < bodyLandmarks[11][0] and \
            bodyLandmarks[15][1] > bodyLandmarks[13][1] and \
            bodyLandmarks[15][0] > bodyLandmarks[12][0]:
        return 5
    # pose 6
    elif bodyLandmarks[16][1] > bodyLandmarks[14][1] and \
            bodyLandmarks[16][0] > bodyLandmarks[14][0] and \
            bodyLandmarks[14][0] < bodyLandmarks[12][0] and \
            bodyLandmarks[14][1] > bodyLandmarks[12][1]and \
            bodyLandmarks[15][1] < bodyLandmarks[13][1] and \
            (abs(bodyLandmarks[15][0] - bodyLandmarks[13][0])) < 0.02 and \
            bodyLandmarks[13][0] > bodyLandmarks[11][0] and \
            (abs(bodyLandmarks[13][1] - bodyLandmarks[11][1])) < 0.02:

        return 6

    else:
        return 0


