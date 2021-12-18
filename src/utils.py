import time
import datetime
import json

import numpy as np
from pygame.surfarray import array3d
import pygame.camera
from nxbt.nxbt import Buttons
from skimage.transform import resize


pygame.camera.init()
# cam = pygame.camera.Camera(pygame.camera.list_cameras()[0])
cam = pygame.camera.Camera("/dev/video2", (720,480))
cam.start()


def get_image(resize=True, resize_width=720, resize_height=480):
    image = cam.get_image()
    image = array3d(image).swapaxes(0,1)
    image = np.array(image)

    # Resize image if option is true and
    # resize width/height don't match image dimensions
    if resize and (resize_width != image.shape[1] or
                   resize_height != image.shape[0]):
        image = resize(image, (resize_height, resize_width))
    
    return image


def wait_for_battle(img_fn, timeout=60, framerate=30, std_threshold=5, rgb_threshold=40):
    battle_frame_count = 0
    timeout_t = time.time()
    while True:
        t = time.time()

        img = img_fn()

        # Get mean std of the image
        red_std = img[:,:,0:1].std()
        green_std = img[:,:,1:2].std()
        blue_std = img[:,:,2:3].std()
        rgb_std_mean = (red_std + green_std + blue_std) / 3

        # Get mean of the image
        red_mean = img[:,:,0:1].mean()
        green_mean = img[:,:,1:2].mean()
        blue_mean = img[:,:,2:3].mean()
        rgb_mean = (red_mean + green_mean + blue_mean) / 3

        if rgb_std_mean < std_threshold and rgb_mean > rgb_threshold:
            battle_frame_count += 1
        else:
            battle_frame_count = 0
        
        if battle_frame_count > 5:
            battle_frame_count = 0
            break

        t = time.time() - t
        sleep_time = 1/framerate - t
        if sleep_time > 0:
            time.sleep(sleep_time)
        
        if time.time() - timeout_t > timeout:
            break


def exit_and_reset(nx, controller_index, stats):
    stats["issues"] += 1
    add_to_stat_log(stats, "Exiting and restting. Attempting to exit to home menu...")
    on_home_menu = False
    while on_home_menu is False:
        press_button(nx, controller_index, "B")
        time.sleep(0.5)
        press_button(nx, controller_index, "B")
        time.sleep(0.5)
        press_button(nx, controller_index, "HOME")
        time.sleep(1)

        # Checking if we're on the home menu
        img = get_image()
        height, width, _ = img.shape
        xl = int(width * 0.0)
        xr = int(width * 0.05)
        yb = int(height * 0.8)
        yt = int(height * 0.7)
        hm_check = img[yt:yb, xl:xr, :]
        hm_mean = hm_check.transpose(2,0,1).mean(axis=(1,2))

        if abs(hm_mean[0] - 55) < 2 and abs(hm_mean[1] - 55) < 2 and abs(hm_mean[2] - 55) < 2:
            add_to_stat_log(stats, "On home menu")
            on_home_menu = True
    
    add_to_stat_log(stats, "Resetting...")
    press_button(nx, controller_index, "X")
    time.sleep(0.75)
    press_button(nx, controller_index, "A")
    time.sleep(3)


def mse(a, b):
    return ((a - b)**2).mean()


def relative_crop(img, left, right, bottom, top):
    height, width, _ = img.shape
    xl = int(width * left)
    xr = int(width * right)
    yb = int(height * bottom)
    yt = int(height * top)
    return img[yt:yb, xl:xr, :]


def add_to_stat_log(stats, msg):
    dt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    msg = f"[{stats['reset_count']}: {dt}] {msg}"

    print(msg)

    stats['log'].append(msg)
    if len(stats['log']) > 100:
        stats['log'].pop(0)
    
    with open("stats.json", "w") as f:
        json.dump(stats, f)


def press_button(nx, controller_indx, button, duration=0.1):
    c_input = nx.create_input_packet()
    c_input[button] = True
    nx.set_controller_input(controller_indx, c_input)
    time.sleep(duration)
    c_input = nx.create_input_packet()
    c_input[button] = False
    nx.set_controller_input(controller_indx, c_input)


def tilt_stick(nx, controller_indx, stick, x, y, duration=1.0):
    c_input = nx.create_input_packet()
    c_input[stick]["X_VALUE"] = x
    c_input[stick]["Y_VALUE"] = y
    nx.set_controller_input(controller_indx, c_input)
    time.sleep(duration)
    c_input = nx.create_input_packet()
    c_input[stick]["X_VALUE"] = 0
    c_input[stick]["Y_VALUE"] = 0
    nx.set_controller_input(controller_indx, c_input)