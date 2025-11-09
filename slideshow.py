import cv2
import os
import numpy as np
import tkinter as tk
from tkinter import simpledialog, messagebox
from threading import Thread
import time

# Folders
with_bg_folder = "rembg_anime_with_bg" #rembg_anime_with_bg / opencv_with_bg
without_bg_folder = "rembg_sam_without_bg" #rembg_anime_without_bg / opencv_without_bg / rembg_sam_without_bg

# Collect base filenames
with_bg_files = sorted([
    f for f in os.listdir(with_bg_folder)
    if f.lower().endswith((".jpg", ".jpeg", ".png"))
])

if not with_bg_files:
    print("❌ No images found in 'with_bg' folder.")
    exit()

# Global variables
index = 0
paused = False
delay = 3  # seconds per slide
start_index = 0
end_index = len(with_bg_files) - 1
stop_thread = False

# ---------------- Helper Functions ----------------
def get_combined_image(base_name):
    """Combine left-right images at original size."""
    with_path = os.path.join(with_bg_folder, f"{base_name}.jpeg")
    if not os.path.exists(with_path):
        with_path = os.path.join(with_bg_folder, f"{base_name}.jpg")
    if not os.path.exists(with_path):
        with_path = os.path.join(with_bg_folder, f"{base_name}.png")

    # without_path = os.path.join(without_bg_folder, f"{base_name}_transparent.png")
    without_path = os.path.join(without_bg_folder, f"rembg_{base_name}.png")
    if not os.path.exists(without_path):
        return None

    img_with = cv2.imread(with_path)
    img_without = cv2.imread(without_path, cv2.IMREAD_UNCHANGED)
    if img_with is None or img_without is None:
        return None

    if img_without.shape[-1] == 4:
        alpha = img_without[:, :, 3]
        img_without = cv2.cvtColor(img_without, cv2.COLOR_BGRA2BGR)
        white_bg = np.ones_like(img_without, dtype=np.uint8) * 255
        mask = alpha == 0
        img_without[mask] = white_bg[mask]

    h1, w1, _ = img_with.shape
    h2, w2, _ = img_without.shape
    max_height = max(h1, h2)
    combined = np.ones((max_height, w1 + w2, 3), dtype=np.uint8) * 255
    combined[:h1, :w1] = img_with
    combined[:h2, w1:w1 + w2] = img_without

    # Add labels
    cv2.putText(combined, "With BG", (30, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    cv2.putText(combined, "Without BG", (w1 + 30, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    return combined

def show_image_thread():
    global index, paused, stop_thread
    while not stop_thread:
        if not paused:
            base_name = os.path.splitext(with_bg_files[index])[0]
            combined = get_combined_image(base_name)
            if combined is not None:
                cv2.imshow("Slideshow GUI (Close window to exit)", combined)
            index += 1
            if index > end_index:
                index = start_index
        key = cv2.waitKey(int(delay * 1000)) & 0xFF
        if key == ord('q'):
            break
    cv2.destroyAllWindows()

# ---------------- GUI Functions ----------------
def play_pause():
    global paused
    paused = not paused
    btn_play_pause.config(text="Play" if paused else "Pause")

def next_image():
    global index
    index += 1
    if index > end_index:
        index = start_index

def prev_image():
    global index
    index -= 1
    if index < start_index:
        index = end_index

def jump_to_image():
    global index
    num = simpledialog.askinteger("Jump to Image", f"Enter image number (1-{len(with_bg_files)}):")
    if num is not None and 1 <= num <= len(with_bg_files):
        index = num - 1
    else:
        messagebox.showwarning("Invalid", "Number out of range!")

def set_range():
    global start_index, end_index, index
    s = simpledialog.askinteger("Start Index", f"Enter start image number (1-{len(with_bg_files)}):")
    e = simpledialog.askinteger("End Index", f"Enter end image number ({s}-{len(with_bg_files)}):")
    if s is None or e is None:
        return
    if 1 <= s <= e <= len(with_bg_files):
        start_index = s - 1
        end_index = e - 1
        index = start_index
    else:
        messagebox.showwarning("Invalid", "Invalid range!")

def on_close():
    global stop_thread
    stop_thread = True
    root.destroy()

# ---------------- Build GUI ----------------
root = tk.Tk()
root.title("Image Slideshow GUI")
root.geometry("400x200")

btn_play_pause = tk.Button(root, text="Pause", width=15, command=play_pause)
btn_play_pause.pack(pady=5)

btn_next = tk.Button(root, text="Next", width=15, command=next_image)
btn_next.pack(pady=5)

btn_prev = tk.Button(root, text="Previous", width=15, command=prev_image)
btn_prev.pack(pady=5)

btn_jump = tk.Button(root, text="Jump to Image", width=15, command=jump_to_image)
btn_jump.pack(pady=5)

btn_range = tk.Button(root, text="Set Range", width=15, command=set_range)
btn_range.pack(pady=5)

root.protocol("WM_DELETE_WINDOW", on_close)

# Start slideshow in a separate thread
thread = Thread(target=show_image_thread, daemon=True)
thread.start()

root.mainloop()
