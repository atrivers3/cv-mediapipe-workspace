import json
import math
import os
from tkinter import filedialog
import tkinter as tk

# Open file dialog so user can choose skeleton.json
root = tk.Tk()
root.withdraw()

INPUT_JSON = filedialog.askopenfilename(
    title="Select skeleton JSON",
    filetypes=[("JSON files", "*.json")]
)

if not INPUT_JSON:
    print("No file selected.")
    exit()

# Output BVH file will be created next to the JSON
OUTPUT_BVH = os.path.splitext(INPUT_JSON)[0] + ".bvh"

# Load animation frames
with open(INPUT_JSON, "r") as f:
    frames = json.load(f)


# VECTOR MATH FUNCTIONS
def vector(a, b):
    # Returns direction vector from point A to point B.
    return [
        b["x"] - a["x"],
        -(b["y"] - a["y"]),
        b["z"] - a["z"]
    ]


def length(v):
    # Compute length of vector.
    return math.sqrt(v[0]**2 + v[1]**2 + v[2]**2)


def normalize(v):
    # Convert vector into unit vector.
    l = length(v)
    if l == 0:
        return [0,0,0]

    return [
        v[0]/l,
        v[1]/l,
        v[2]/l
    ]


def vector_to_euler(v):
    # Convert a direction vector into Euler angles.
    v = normalize(v)

    # yaw = rotation left/right
    yaw = math.degrees(math.atan2(v[0], v[2]))

    # pitch = rotation up/down
    pitch = math.degrees(math.atan2(v[1], math.sqrt(v[0]**2 + v[2]**2)))

    # roll = twist (not available from single vector)
    roll = 0

    return [pitch, yaw, roll]


# BVH SKELETON HIERARCHY
# ---------------------------------------------------------
hierarchy = """
HIERARCHY
ROOT Hips
{
OFFSET 0 0 0
CHANNELS 6 Xposition Yposition Zposition Zrotation Xrotation Yrotation

JOINT LeftArm
{
OFFSET 5 10 0
CHANNELS 3 Zrotation Xrotation Yrotation

JOINT LeftForeArm
{
OFFSET 0 10 0
CHANNELS 3 Zrotation Xrotation Yrotation

JOINT LeftHand
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

JOINT RightArm
{
OFFSET -5 10 0
CHANNELS 3 Zrotation Xrotation Yrotation

JOINT RightForeArm
{
OFFSET 0 10 0
CHANNELS 3 Zrotation Xrotation Yrotation

JOINT RightHand
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


# ---------------------------------------------------------
# GENERATE MOTION DATA
# ---------------------------------------------------------

motion_lines = []

for frame in frames:

    joints = frame["joints"]
    root = frame["root"]

    motion = []

    # Root position
    motion.extend([
        root["x"] * 100,
        -(root["y"] * 100),
        root["z"] * 100,
        0,0,0
    ])

    # LEFT ARM ROTATION
    if "left_shoulder" in joints and "left_elbow" in joints:

        v = vector(joints["left_shoulder"], joints["left_elbow"])
        motion += vector_to_euler(v)
    else:
        motion += [0,0,0]


    if "left_elbow" in joints and "LeftWrist" in joints:

        v = vector(joints["left_elbow"], joints["LeftWrist"])
        motion += vector_to_euler(v)
    else:
        motion += [0,0,0]


    motion += [0,0,0]  # LeftHand rotation


    # RIGHT ARM ROTATION
    if "right_shoulder" in joints and "right_elbow" in joints:

        v = vector(joints["right_shoulder"], joints["right_elbow"])
        motion += vector_to_euler(v)
    else:
        motion += [0,0,0]


    if "right_elbow" in joints and "RightWrist" in joints:

        v = vector(joints["right_elbow"], joints["RightWrist"])
        motion += vector_to_euler(v)
    else:
        motion += [0,0,0]

    motion += [0,0,0]  # RightHand rotation
    motion_lines.append(" ".join(str(round(v,4)) for v in motion))


# WRITE BVH FILE
with open(OUTPUT_BVH,"w") as f:

    f.write(hierarchy)

    f.write("\nMOTION\n")
    f.write(f"Frames: {len(motion_lines)}\n")
    f.write("Frame Time: 0.04\n")

    for line in motion_lines:
        f.write(line+"\n")


print("BVH saved to:", OUTPUT_BVH)