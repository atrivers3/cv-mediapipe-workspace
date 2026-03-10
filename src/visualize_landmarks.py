import cv2
import mediapipe as mp
import os
import tkinter as tk
from tkinter import filedialog


# Setup Project Paths
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")

os.makedirs(OUTPUT_DIR, exist_ok=True)


# Select Video
# -----------------------------

root = tk.Tk()
root.withdraw()

video_path = filedialog.askopenfilename(
    title="Select a Video File",
    filetypes=[("Video files", "*.mp4 *.avi *.mov *.mkv")]
)

if not video_path:
    print("No file selected.")
    exit()

video_filename = os.path.splitext(os.path.basename(video_path))[0]

output_video = os.path.join(OUTPUT_DIR, f"{video_filename}_landmarks.mp4")

# Initialize MediaPipe Holistic
mp_holistic = mp.solutions.holistic
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

holistic = mp_holistic.Holistic(
    min_detection_confidence=0.3,     # was 0.5, lower makes it more sensitive
    min_tracking_confidence=0.3,      # was 0.5
    model_complexity=2,
    refine_face_landmarks=False       # we don't need eye iris
)


cap = cv2.VideoCapture(video_path)

# Get video properties for output video
width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps    = cap.get(cv2.CAP_PROP_FPS)

# Output video with drawn landmarks
out = cv2.VideoWriter(output_video, 
                      cv2.VideoWriter_fourcc(*'mp4v'), 
                      fps, 
                      (width, height))

frame_idx = 0

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    
    # COnvert to RGB
    image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    image.flags.writeable = False   #lock image temporarily

    results = holistic.process(image) #detect body, face, hand poses of a frame

    # Convert back to BGR for drawing & saving
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    # Draw pose
    if results.pose_landmarks:
        mp_drawing.draw_landmarks(
            image,
            results.pose_landmarks, #contain Landmarsk of Pose
            mp_holistic.POSE_CONNECTIONS, #Blueprint that connect landmarks(dots)
            landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style()
        )

    # Draw left hand (if detected)
    if results.left_hand_landmarks:
        mp_drawing.draw_landmarks(
            image,
            results.left_hand_landmarks, #contain Landmarsk of left hand
            mp_holistic.HAND_CONNECTIONS,
            mp_drawing_styles.get_default_hand_landmarks_style(), #Set Dots to every Landmark
            mp_drawing_styles.get_default_hand_connections_style() #Set default thickness and color for Skeleton Lines
        )

    # Draw right hand
    if results.right_hand_landmarks:
        mp_drawing.draw_landmarks(
            image,
            results.right_hand_landmarks, #contain Landmarsk of right hand
            mp_holistic.HAND_CONNECTIONS,
            mp_drawing_styles.get_default_hand_landmarks_style(),
            mp_drawing_styles.get_default_hand_connections_style()
        )

    # Optional: show frame number (helps correlate with JSON)
    cv2.putText(image, f"Frame: {frame_idx}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    out.write(image)  # save to video

    # live preview
    cv2.imshow("Holistic Preview", image)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

    frame_idx += 1

# Cleanup
cap.release()
out.release()
holistic.close()
cv2.destroyAllWindows()

print("Processed frames:", frame_idx)
print("Saved video to:", output_video)