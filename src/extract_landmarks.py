import cv2
import mediapipe as mp
import json
import os
import tkinter as tk
from tkinter import filedialog

# Setup Project Paths
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Select Video File
root = tk.Tk()
root.withdraw()

video_path = filedialog.askopenfilename(
    title="Select a Video File",
    filetypes=[("Video files", "*.mp4 *.avi *.mov *.mkv")]
)

if not video_path:
    print("No file selected. Exiting...")
    exit()

video_filename = os.path.splitext(os.path.basename(video_path))[0]
output_json = os.path.join(OUTPUT_DIR, f"{video_filename}.json")


# Initialize MediaPipe Holistic
mp_holistic = mp.solutions.holistic

holistic = mp_holistic.Holistic(
    min_detection_confidence=0.3,  # Lowered for hands in sign language
    min_tracking_confidence=0.3,
    model_complexity=2
)

cap = cv2.VideoCapture(video_path)

all_landmarks = []
frame_count = 0

while cap.isOpened():

    ret, frame = cap.read() #ret = True if frame exists.

    if not ret:
        break

    image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) #COnvert BGR(OpenCV reads) to RGB(MediaPipe expects) 
    image.flags.writeable = False   # prevents copying memory

    results = holistic.process(image) # process and return landmarks: pose_landmarks, left_hand_landmarks, right_hand_landmarks

    frame_landmarks = {
        "frame": frame_count,
        "pose": [],
        "left_hand": [],
        "right_hand": []
    }

    if results.pose_landmarks:
        for idx, lm in enumerate(results.pose_landmarks.landmark):  #Loop through 33 Body points
            frame_landmarks["pose"].append({
                "id": idx,
                "x": lm.x,
                "y": lm.y,
                "z": lm.z,
                "visibility": lm.visibility    # Visibility tells how confident the model is that the point is visible.
            })


    if results.left_hand_landmarks:
        for idx, lm in enumerate(results.left_hand_landmarks.landmark): #Loop through 21 left hand points
            frame_landmarks["left_hand"].append({
                "id": idx,
                "x": lm.x,
                "y": lm.y,
                "z": lm.z,
            })

    if results.right_hand_landmarks:
        for idx, lm in enumerate(results.right_hand_landmarks.landmark): #Loop through 21 left hand points
            frame_landmarks["right_hand"].append({
                "id": idx,
                "x": lm.x,
                "y": lm.y,
                "z": lm.z,
            })

    all_landmarks.append(frame_landmarks)

    frame_count += 1

#Clean up memory
cap.release()
holistic.close()


# Save JSON
with open(output_json, "w") as f:
    json.dump(all_landmarks, f, indent=4)

print("Frames processed:", frame_count)
print("Saved JSON to:", output_json)
