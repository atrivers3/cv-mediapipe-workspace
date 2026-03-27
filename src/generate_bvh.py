import json
import math
import os
import tkinter as tk
from tkinter import filedialog
from collections import defaultdict

#  FILE SELECTION
root = tk.Tk()
root.withdraw() # Hides the main empty tkinter window
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

print(f"Loaded {len(frames)} frames")

#  HELPERS 
def vector(p, c):
    return [c["x"] - p["x"], -(c["y"] - p["y"]), c["z"] - p["z"]]

def length(v):
    # 3D Pythagorean theorem (d^2 = a^2 + b^2 + c^2)
    return math.sqrt(v[0]**2 + v[1]**2 + v[2]**2)

def normalize(v):
    # Keeping the arrow pointing in the exact same direction, but shrinking its length is exactly 1. 
    l = length(v)
    return [v[0]/l, v[1]/l, v[2]/l] if l > 1e-6 else [0,0,0]

def to_euler(v):
    """
    'Euler angles' are the actual X, Y, Z rotations you see in software like Blender.
    - Yaw is turning left/right.
    - Pitch is tilting up/down.
    (Roll is set to 0.0 here).
    """
    n = normalize(v)
    yaw = math.degrees(math.atan2(n[0], n[2]))
    horiz = math.sqrt(n[0]**2 + n[2]**2)
    pitch = math.degrees(math.atan2(n[1], horiz))
    return [pitch * 0.8, yaw * 0.8, 0.0]

# ====================== SCALE & LENGTHS ======================
def compute_scale():
    """
    NOTE: AI tracking often measures things in tiny numbers (like 0.5 meters).
    BVH files often expect bigger units (like centimeters).
    This function looks at the shoulders. If the AI says the shoulders are 0.5 apart, 
    but we want them to be 80 units wide in BVH, it calculates a multiplier (SCALE) 
    so our skeleton isn't tiny.
    """
    for f in frames[:30]:
        j = f["joints"]
        if "left_shoulder" in j and "right_shoulder" in j:
            d = length(vector(j["left_shoulder"], j["right_shoulder"]))
            if d > 0.05:
                return 80 / d   # Target ~80 units shoulder width in BVH
    return 60.0

SCALE = compute_scale()
print(f"Using scale: {SCALE:.2f}")

def avg_length(parent_name, child_name):
    """
    BVH needs ONE permanent bone length. This looks at the first 50 frames, 
    calculates the distance every time, and finds the average length to build our rigid skeleton.
    """
    vals = []
    for f in frames[:50]:
        j = f["joints"]
        p = j.get(parent_name)
        c = j.get(child_name)
        if p and c:
            vals.append(length(vector(p, c)))
    return (sum(vals) / len(vals)) * SCALE if vals else 4.0

# ====================== HIERARCHY ======================
# Hierarchy section defines the "T-Pose" or resting state of the skeleton.
def finger_block(side):
    return f"""
        JOINT {side}Thumb1 {{ OFFSET 0 {avg_length(f"{side}Wrist", f"{side}ThumbProximal"):.2f} 0 CHANNELS 3 Zrotation Xrotation Yrotation
            JOINT {side}Thumb2 {{ OFFSET 0 {avg_length(f"{side}ThumbProximal", f"{side}ThumbIntermediate"):.2f} 0 CHANNELS 3 Zrotation Xrotation Yrotation
                JOINT {side}Thumb3 {{ OFFSET 0 {avg_length(f"{side}ThumbIntermediate", f"{side}ThumbDistal"):.2f} 0 CHANNELS 3 Zrotation Xrotation Yrotation
                    End Site {{ OFFSET 0 2 0 }}
                }}
            }}
        }}
        JOINT {side}Index1 {{ OFFSET 0 {avg_length(f"{side}Wrist", f"{side}IndexProximal"):.2f} 0 CHANNELS 3 Zrotation Xrotation Yrotation
            JOINT {side}Index2 {{ OFFSET 0 {avg_length(f"{side}IndexProximal", f"{side}IndexIntermediate"):.2f} 0 CHANNELS 3 Zrotation Xrotation Yrotation
                JOINT {side}Index3 {{ OFFSET 0 {avg_length(f"{side}IndexIntermediate", f"{side}IndexDistal"):.2f} 0 CHANNELS 3 Zrotation Xrotation Yrotation
                    End Site {{ OFFSET 0 2 0 }}
                }}
            }}
        }}
        JOINT {side}Middle1 {{ OFFSET 0 {avg_length(f"{side}Wrist", f"{side}MiddleProximal"):.2f} 0 CHANNELS 3 Zrotation Xrotation Yrotation
            JOINT {side}Middle2 {{ OFFSET 0 {avg_length(f"{side}MiddleProximal", f"{side}MiddleIntermediate"):.2f} 0 CHANNELS 3 Zrotation Xrotation Yrotation
                JOINT {side}Middle3 {{ OFFSET 0 {avg_length(f"{side}MiddleIntermediate", f"{side}MiddleDistal"):.2f} 0 CHANNELS 3 Zrotation Xrotation Yrotation
                    End Site {{ OFFSET 0 2 0 }}
                }}
            }}
        }}
        JOINT {side}Ring1 {{ OFFSET 0 {avg_length(f"{side}Wrist", f"{side}RingProximal"):.2f} 0 CHANNELS 3 Zrotation Xrotation Yrotation
            JOINT {side}Ring2 {{ OFFSET 0 {avg_length(f"{side}RingProximal", f"{side}RingIntermediate"):.2f} 0 CHANNELS 3 Zrotation Xrotation Yrotation
                JOINT {side}Ring3 {{ OFFSET 0 {avg_length(f"{side}RingIntermediate", f"{side}RingDistal"):.2f} 0 CHANNELS 3 Zrotation Xrotation Yrotation
                    End Site {{ OFFSET 0 2 0 }}
                }}
            }}
        }}
        JOINT {side}Pinky1 {{ OFFSET 0 {avg_length(f"{side}Wrist", f"{side}PinkyProximal"):.2f} 0 CHANNELS 3 Zrotation Xrotation Yrotation
            JOINT {side}Pinky2 {{ OFFSET 0 {avg_length(f"{side}PinkyProximal", f"{side}PinkyIntermediate"):.2f} 0 CHANNELS 3 Zrotation Xrotation Yrotation
                JOINT {side}Pinky3 {{ OFFSET 0 {avg_length(f"{side}PinkyIntermediate", f"{side}PinkyDistal"):.2f} 0 CHANNELS 3 Zrotation Xrotation Yrotation
                    End Site {{ OFFSET 0 2 0 }}
                }}
            }}
        }}
"""

hierarchy = f"""
HIERARCHY
ROOT Hips
{{
    OFFSET 0 0 0
    CHANNELS 6 Xposition Yposition Zposition Zrotation Xrotation Yrotation

    JOINT Spine {{ OFFSET 0 {SCALE*0.08:.2f} 0 CHANNELS 3 Zrotation Xrotation Yrotation

        JOINT LeftShoulder {{ OFFSET {SCALE*0.06:.2f} 0 0 CHANNELS 3 Zrotation Xrotation Yrotation
            JOINT LeftArm {{ OFFSET 0 {avg_length("left_shoulder","left_elbow"):.2f} 0 CHANNELS 3 Zrotation Xrotation Yrotation
                JOINT LeftForeArm {{ OFFSET 0 {avg_length("left_elbow","left_wrist"):.2f} 0 CHANNELS 3 Zrotation Xrotation Yrotation
                    {finger_block("Left")}
                }}
            }}
        }}

        JOINT RightShoulder {{ OFFSET -{SCALE*0.06:.2f} 0 0 CHANNELS 3 Zrotation Xrotation Yrotation
            JOINT RightArm {{ OFFSET 0 {avg_length("right_shoulder","right_elbow"):.2f} 0 CHANNELS 3 Zrotation Xrotation Yrotation
                JOINT RightForeArm {{ OFFSET 0 {avg_length("right_elbow","right_wrist"):.2f} 0 CHANNELS 3 Zrotation Xrotation Yrotation
                    {finger_block("Right")}
                }}
            }}
        }}
    }}
}}
"""

def smooth(prev, curr, alpha=0.7):
    return [
        prev[i]*alpha + curr[i]*(1-alpha)
        for i in range(3)
    ]

# ====================== MOTION ======================
motion_lines = []
last_rot = [0.0, 0.0, 0.0]   # global fallback

for frame in frames:
    j = frame.get("joints", {})
    root = frame.get("root", {"x":0, "y":0, "z":0})

    # motion = [HipPosX, HipPosY, HipPosZ, HipRotZ, HipRotX, HipRotY, SpineRotZ, SpineRotX, SpineRotY]
    motion = [
        root["x"] * SCALE,           # 1. Hip Position X
        (root["y"] + 1.8) * SCALE,   # 2. Hip Position Y (Lift the hips up so feet don't clip through the floor)
        root["z"] * SCALE,           # 3. Hip Position Z
        0, 0, 0,                     # 4, 5, 6. Hip Rotation (Z, X, Y) (Because we have Half body movement in the videos)
        0, 0, 0                      # 7, 8, 9. Spine Rotation (Z, X, Y) (Because we have Half body movement in the videos)
    ]

    # LEFT ARM (This Loop run 2 times so after those 9 values 3 on each iteration add, 1st time for left shoulder 2nd time for left elbow)
    for parent, child in [("left_shoulder", "left_elbow"), ("left_elbow", "left_wrist")]:
        if parent in j and child in j:
            rot = to_euler(vector(j[parent], j[child]))
            last_rot = rot
            motion += rot
        else:
            motion += last_rot

    # LEFT FINGERS (5 separate chains)
    left_chains = [
        ["LeftWrist", "LeftThumbProximal", "LeftThumbIntermediate", "LeftThumbDistal"],
        ["LeftWrist", "LeftIndexProximal", "LeftIndexIntermediate", "LeftIndexDistal"],
        ["LeftWrist", "LeftMiddleProximal", "LeftMiddleIntermediate", "LeftMiddleDistal"],
        ["LeftWrist", "LeftRingProximal", "LeftRingIntermediate", "LeftRingDistal"],
        ["LeftWrist", "LeftPinkyProximal", "LeftPinkyIntermediate", "LeftPinkyDistal"]
    ]
    for chain in left_chains:
        for i in range(len(chain)-1):
            p = j.get(chain[i])
            c = j.get(chain[i+1])
            if p and c:
                new_rot = to_euler(vector(p, c))
                rot = smooth(last_rot, new_rot)
                last_rot = rot
                last_rot = rot
                motion += rot
            else:
                motion += last_rot

    # RIGHT ARM
    for parent, child in [("right_shoulder", "right_elbow"), ("right_elbow", "right_wrist")]:
        if parent in j and child in j:
            rot = to_euler(vector(j[parent], j[child]))
            last_rot = rot
            motion += rot
        else:
            motion += last_rot

    # RIGHT FINGERS
    right_chains = [
        ["RightWrist", "RightThumbProximal", "RightThumbIntermediate", "RightThumbDistal"],
        ["RightWrist", "RightIndexProximal", "RightIndexIntermediate", "RightIndexDistal"],
        ["RightWrist", "RightMiddleProximal", "RightMiddleIntermediate", "RightMiddleDistal"],
        ["RightWrist", "RightRingProximal", "RightRingIntermediate", "RightRingDistal"],
        ["RightWrist", "RightPinkyProximal", "RightPinkyIntermediate", "RightPinkyDistal"]
    ]
    for chain in right_chains:
        for i in range(len(chain)-1):
            p = j.get(chain[i])
            c = j.get(chain[i+1])
            if p and c:
                new_rot = to_euler(vector(p, c))
                rot = smooth(last_rot, new_rot)
                last_rot = rot
                last_rot = rot
                motion += rot
            else:
                motion += last_rot

    motion_lines.append(" ".join(f"{round(x,4)}" for x in motion))


# ====================== WRITE ======================
with open(OUTPUT_BVH, "w") as f:
    f.write(hierarchy)
    f.write("\nMOTION\n")
    f.write(f"Frames: {len(motion_lines)}\n")
    f.write("Frame Time: 0.04\n")
    for line in motion_lines:
        f.write(line + "\n")

print(f"✅ FIXED BVH: {OUTPUT_BVH}")
print("   - Full hand chains (no cross-finger linking)")
print("   - Uses hand wrist for fingers, pose wrist for arm")
print("   - Scale tuned + ground offset")
print("   - Fallback rotations = smooth motion")