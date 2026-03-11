import json
import math
import os
from collections import defaultdict
from tkinter import filedialog
import tkinter as tk

# Project paths (adapt to your structure)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

root = tk.Tk()
root.withdraw()

INPUT_JSON = filedialog.askopenfilename(
    title="Select landmarks JSON",
    filetypes=[("JSON files", "*.json")]
)

if not INPUT_JSON:
    print("No file selected. Exiting...")
    exit()

JSON_filename = os.path.splitext(os.path.basename(INPUT_JSON))[0]
JSON_filename+="_skeleton"
OUTPUT_JSON = os.path.join(OUTPUT_DIR, f"{JSON_filename}.json")


# Key landmark IDs we care about
POSE_KEYS = {
    "left_shoulder": 11,
    "right_shoulder": 12,
    "left_elbow": 13,
    "right_elbow": 14,
    "left_wrist": 15,
    "right_wrist": 16,
    "left_hip": 23,
    "right_hip": 24,
    #Pose keys: https://developers.google.com/mediapipe/solutions/vision/pose_landmarker
}

# Hand landmarks always have 21 points
# 0 = wrist
# 1-4 = thumb
# 5-8 = index
HAND_IDS = list(range(21)) 

# Semantic names for fingers
FINGER_NAMES = {
    0: "Wrist",
    1: "ThumbProximal",    # cmc
    2: "ThumbIntermediate",# mcp
    3: "ThumbDistal",      # ip
    4: "ThumbTip",
    5: "IndexProximal",
    6: "IndexIntermediate",
    7: "IndexDistal",
    8: "IndexTip",
    9: "MiddleProximal",
    10: "MiddleIntermediate",
    11: "MiddleDistal",
    12: "MiddleTip",
    13: "RingProximal",
    14: "RingIntermediate",
    15: "RingDistal",
    16: "RingTip",
    17: "PinkyProximal",
    18: "PinkyIntermediate",
    19: "PinkyDistal",
    20: "PinkyTip",
}

# It checks the dictionary. If the ID exists, it gives you the coordinates.
def get_landmark(pose_dict, id_, default=None):
    return pose_dict.get(id_, default)

# Compute 3D distance between two landmarks, used to estimate body scale(eg shoulder width)
def distance(a, b):
    if not a or not b: return 0.0
    return math.sqrt(
        (a["x"] - b["x"])**2 +
        (a["y"] - b["y"])**2 +
        (a["z"] - b["z"])**2
    )

# Used to calculate body root (hip center)
def midpoint(a, b):
    if not a or not b: return {"x":0, "y":0, "z":0}
    return {
        "x": (a["x"] + b["x"]) / 2,
        "y": (a["y"] + b["y"]) / 2,
        "z": (a["z"] + b["z"]) / 2
    }

def subtract(a, b):
    return {"x": a["x"] - b["x"], "y": a["y"] - b["y"], "z": a["z"] - b["z"]}

# Normalize coordinates so we can get the same body size even if person or camera distance change
def normalize_point(p, root, scale):
 
    if scale <= 1e-6: scale = 1.0  # prevent division by zero
    return {
        "x": (p["x"] - root["x"]) / scale,
        "y": (p["y"] - root["y"]) / scale,
        "z": (p["z"] - root["z"]) / scale
    }


# Main
with open(INPUT_JSON, "r") as f:
    frames = json.load(f)

output_frames = []
scale_history = []          # collect good scales for fallback
reference_bone_lengths = {} # will compute once from first good frame

for frame_data in frames:
    frame_num = frame_data["frame"]
    pose_list = frame_data.get("pose", [])
    left_hand_list = frame_data.get("left_hand", [])
    right_hand_list = frame_data.get("right_hand", [])

    # COnvert into dictionaries 
    pose = {p["id"]: p for p in pose_list}
    left_hand = {p["id"]: p for p in left_hand_list}
    right_hand = {p["id"]: p for p in right_hand_list}

    # Get core landmarks with safety
    l_hip = get_landmark(pose, POSE_KEYS["left_hip"])
    r_hip = get_landmark(pose, POSE_KEYS["right_hip"])
    l_shoulder = get_landmark(pose, POSE_KEYS["left_shoulder"])
    r_shoulder = get_landmark(pose, POSE_KEYS["right_shoulder"])

    # If critical landmarks are missing then skip frame
    if not (l_hip and r_hip and l_shoulder and r_shoulder):
        print(f"Frame {frame_num}: missing core body landmarks → skipping")
        continue

    # Visibility check for pose(If Low visibility means unreliable)
    if (l_hip["visibility"] < 0.4 or r_hip["visibility"] < 0.4 or
        l_shoulder["visibility"] < 0.5 or r_shoulder["visibility"] < 0.5):
        print(f"Frame {frame_num}: low visibility on core → skipping")
        continue

    root = midpoint(l_hip, r_hip) # center of hip
    current_scale = distance(l_shoulder, r_shoulder)    # Calculate Scale for current frame

    if current_scale > 0.01:  # reasonable threshold
        scale_history.append(current_scale)
    else:
        if scale_history:   # use average of previous scales
            current_scale = sum(scale_history) / len(scale_history)
        else:
            current_scale = 0.2  # fallback initial guess

    # Build skeleton dict with semantic names
    skeleton = {}

    # Body joints
    for name, pid in POSE_KEYS.items():
        lm = get_landmark(pose, pid)
        if lm:
            skeleton[name] = normalize_point(lm, root, current_scale)

    # Hands – full 21 per side
    for side, hand_dict in [("left", left_hand), ("right", right_hand)]:
        for hid in HAND_IDS:
            lm = hand_dict.get(hid)
            if lm:
                fname = FINGER_NAMES.get(hid, f"_{hid}")
                key = f"{side.capitalize()}{fname}"
                skeleton[key] = normalize_point(lm, root, current_scale)

    # Also store raw root position (scaled) for BVH root motion
    scaled_root = {
        "x": root["x"] / current_scale,
        "y": root["y"] / current_scale,
        "z": root["z"] / current_scale
    }

    output_frames.append({
        "frame": frame_num,
        "root": scaled_root,
        "joints": skeleton
    })



print(f"Processed {len(output_frames)} / {len(frames)} frames")
with open(OUTPUT_JSON, "w") as f:
    json.dump(output_frames, f, indent=4)

print(f"Saved normalized skeleton to: {OUTPUT_JSON}")