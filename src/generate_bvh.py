import json
import math
import os
from tkinter import filedialog
import tkinter as tk

# Select normalized skeleton JSON
root = tk.Tk()
root.withdraw()

INPUT_JSON = filedialog.askopenfilename(
    title="Select normalized skeleton JSON",
    filetypes=[("JSON files", "*.json")]
)

if not INPUT_JSON:
    print("No file selected.")
    exit()

OUTPUT_BVH = os.path.splitext(INPUT_JSON)[0] + ".bvh"

with open(INPUT_JSON, "r") as f:
    frames = json.load(f)

# -------------------------
# Helper math functions
# -------------------------

# def vector(a, b):
#     return [
#         b["x"] - a["x"],
#         b["y"] - a["y"],
#         b["z"] - a["z"]
#     ]

def vector(a, b):
    # We add a negative sign to the Y-axis to flip MediaPipe's coordinates 
    # to match standard 3D space
    return [
        b["x"] - a["x"],
        -(b["y"] - a["y"]), 
        b["z"] - a["z"]
    ]

def length(v):
    return math.sqrt(v[0]**2 + v[1]**2 + v[2]**2)

def normalize(v):
    l = length(v)
    if l == 0:
        return [0,0,0]
    return [v[0]/l, v[1]/l, v[2]/l]

def vector_to_euler(v):
    v = normalize(v)

    yaw = math.degrees(math.atan2(v[0], v[2]))
    pitch = math.degrees(math.atan2(v[1], math.sqrt(v[0]**2 + v[2]**2)))
    roll = 0

    return [pitch, yaw, roll]

# -------------------------
# Build BVH hierarchy
# -------------------------

hierarchy = """
HIERARCHY
ROOT Hips
{
OFFSET 0 0 0
CHANNELS 6 Xposition Yposition Zposition Zrotation Xrotation Yrotation

JOINT LeftShoulder
{
OFFSET 5 10 0
CHANNELS 3 Zrotation Xrotation Yrotation

JOINT LeftElbow
{
OFFSET 0 10 0
CHANNELS 3 Zrotation Xrotation Yrotation

JOINT LeftWrist
{
OFFSET 0 10 0
CHANNELS 3 Zrotation Xrotation Yrotation

End Site
{
OFFSET 0 5 0
}
}
}
}

JOINT RightShoulder
{
OFFSET -5 10 0
CHANNELS 3 Zrotation Xrotation Yrotation

JOINT RightElbow
{
OFFSET 0 10 0
CHANNELS 3 Zrotation Xrotation Yrotation

JOINT RightWrist
{
OFFSET 0 10 0
CHANNELS 3 Zrotation Xrotation Yrotation

End Site
{
OFFSET 0 5 0
}
}
}
}
}
"""

# -------------------------
# Motion frames
# -------------------------

motion_lines = []

for frame in frames:

    joints = frame["joints"]

    root = frame["root"]

    motion = []

    motion.extend([
        root["x"] * 10,
        -(root["y"] * 10),
        root["z"] * 10,
        0,0,0
    ])

    if "left_shoulder" in joints and "left_elbow" in joints:

        v = vector(joints["left_shoulder"], joints["left_elbow"])
        motion += vector_to_euler(v)

    else:
        motion += [0,0,0]

    if "left_elbow" in joints and "left_wrist" in joints:

        v = vector(joints["left_elbow"], joints["left_wrist"])
        motion += vector_to_euler(v)

    else:
        motion += [0,0,0]

    motion += [0,0,0]

    if "right_shoulder" in joints and "right_elbow" in joints:

        v = vector(joints["right_shoulder"], joints["right_elbow"])
        motion += vector_to_euler(v)

    else:
        motion += [0,0,0]

    if "right_elbow" in joints and "right_wrist" in joints:

        v = vector(joints["right_elbow"], joints["right_wrist"])
        motion += vector_to_euler(v)

    else:
        motion += [0,0,0]

    motion += [0,0,0]

    motion_lines.append(" ".join(str(round(v,4)) for v in motion))

# -------------------------
# Write BVH
# -------------------------

with open(OUTPUT_BVH,"w") as f:

    f.write(hierarchy)

    f.write("\nMOTION\n")
    f.write(f"Frames: {len(motion_lines)}\n")
    f.write("Frame Time: 0.04\n")

    for line in motion_lines:
        f.write(line+"\n")

print("BVH saved to:", OUTPUT_BVH)