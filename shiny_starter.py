import time
import json
import os

from src.utils import *
from src.notify import send_message

import numpy as np
from PIL import Image
import nxbt


TURTWIG = 0
CHIMCHAR = 1
PIPLUP = 2


def detect_shiny_starter(img_fn, timeout=17, framerate=30, timing_threshold=11.55):
    hp_bar_time = time.time()
    timeout_start = time.time()
    while time.time() - timeout_start < timeout:
        t = time.time()

        img = img_fn()

        # Get the opponents health bar image region
        height, width, _ = img.shape
        xl = int(width * 0.90)
        xr = int(width * 0.96)
        yb = int(height * 0.13)
        yt = int(height * 0.115)
        hp_bar = img[yt:yb, xl:xr, :]

        # Get the mean of the hp bar
        red_mean = hp_bar[:,:,0:1].mean()
        green_mean = hp_bar[:,:,1:2].mean()
        blue_mean = hp_bar[:,:,2:3].mean()

        # Get the diff of the hp_bar's channels
        # from the expected hp_bar colour
        red_diff = abs(red_mean - 100)
        green_diff = abs(green_mean - 200)
        blue_diff = abs(blue_mean - 100)

        # Check diffs
        if red_diff < 35 and green_diff < 35 and blue_diff < 35:
            appearance_time = time.time() - hp_bar_time
            print("Appearance time", appearance_time)
            if appearance_time > timing_threshold:
                print("Shiny detected")
                return True
            break

        # print(red_mean, green_mean, blue_mean, red_diff, green_diff, blue_diff)
        
        t = time.time() - t
        sleep_time = 1/framerate - t
        if sleep_time > 0:
            time.sleep(sleep_time)
    
    return False


def reset_hunt():
    stats = None
    if os.path.isfile("stats.json"):
        with open("stats.json", "r") as f:
            stats = json.load(f)
    else:
        stats = {
            "reset_count": 0,
            "issues": 0,
            "log": []
        }

    pokemon = TURTWIG

    starter_select_check = np.array(Image.open("./check-imgs/starter-select-check.png"))
    yes_select_check = np.array(Image.open("./check-imgs/yes-select-check.png"))
    hand_turtwig = np.array(Image.open("./check-imgs/hand-turtwig.png"))
    hand_chimchar = np.array(Image.open("./check-imgs/hand-chimchar.png"))
    hand_piplup = np.array(Image.open("./check-imgs/hand-piplup.png"))

    # Initialize an emulated controller and connect
    # to an available Switch.
    nx = nxbt.Nxbt()
    controller_index = nx.create_controller(
        nxbt.PRO_CONTROLLER,
        reconnect_address=nx.get_switch_addresses())
    nx.wait_for_connection(controller_index)

    add_to_stat_log(stats, "Controller Connected")

    # Activate controller and wait for Switch to recognize it
    nx.macro(controller_index, "B 0.1s\n 0.1s")
    nx.macro(controller_index, "B 0.1s\n 0.1s")
    nx.macro(controller_index, "B 0.1s\n 0.1s")

    while True:
        add_to_stat_log(stats, f"Reset Count {stats['reset_count']}")

        # Assume we are on the Home screen with BDSP selected
        press_button(nx, controller_index, "A")
        time.sleep(1.3)
        press_button(nx, controller_index, "A")
        time.sleep(0.5)
        press_button(nx, controller_index, "A")
        time.sleep(0.5)
        press_button(nx, controller_index, "A")
        time.sleep(2)

        # Wait for the game to boot
        game_loading = False
        game_loaded = False
        t = time.time()
        while game_loaded is not True:
            img = get_image()

            loading_mean = np.mean(relative_crop(img, 0.0, 0.025, 1.0, 0.975))

            if time.time() - t > 80:
                add_to_stat_log(stats, "Something went wrong. Game load > 80s.")
                exit_and_reset(nx, controller_index, stats)

            # Check if the game crashed
            # Get independent means of r, g, and b
            rgb_means = np.mean(relative_crop(img, 0.0, 0.025, 1.0, 0.975), (0,1))
            if abs(rgb_means[0] - 55) < 2 and abs(rgb_means[1] - 55) < 2 and abs(rgb_means[2] - 55) < 2:
                add_to_stat_log(stats, "Game crashed...")
                game_loading = False
                game_loaded = False
                press_button(nx, controller_index, "A")
                time.sleep(2)


            # Check if the game is loading
            if game_loading is False and loading_mean < 18:
                add_to_stat_log(stats, "Game is loading...")
                game_loading = True

            # Check if we've exited the loader
            if game_loading and loading_mean >= 18:
                add_to_stat_log(stats, "Game is loaded")
                game_loaded = True
            # If we haven't, keep pressing A
            else:
                press_button(nx, controller_index, "A")

        # Wait a bit to make sure the game has fully loaded in
        time.sleep(2)

        # Move up once on the dpad
        add_to_stat_log(stats, "Moving up...")
        tilt_stick(nx, controller_index, "L_STICK", 0, 100)

        # Wait for rival to talk
        time.sleep(1)

        # Skip dialogue and enter
        press_button(nx, controller_index, "A")

        # Wait for scene to load in
        time.sleep(3)

        # Mash A until we see a black screen
        # which signals that we're choosing a pokemon
        add_to_stat_log(stats, "Skipping dialogue...")
        t = time.time()
        select_loading = False
        select_loaded = False
        while select_loaded is not True:
            img = get_image()
            select_mean = np.mean(img)

            if time.time() - t > 70:
                add_to_stat_log(stats, "Something went wrong. Dialogue > 70s.")
                exit_and_reset(nx, controller_index, stats)

            # Check if the game is loading
            if select_loading is False and select_mean < 18:
                add_to_stat_log(stats, "Entering selection screen...")
                select_loading = True

            # Check if we've exited the loader
            if select_loading and select_mean >= 18:
                add_to_stat_log(stats, "Entered selection screen")
                select_loaded = True
            # If we haven't, keep pressing A
            else:
                press_button(nx, controller_index, "A")

        # Check that we are on the starter selection screen
        time.sleep(5)
        img = relative_crop(get_image(), 0.7, 0.75, 0.95, 0.92)
        img_mse = mse(starter_select_check, img)
        add_to_stat_log(stats, f"Starter MSE: {img_mse}")
        if img_mse > 15:
            add_to_stat_log(stats, "Something went wrong. Not on starter selection.")
            exit_and_reset(nx, controller_index, stats)
            continue
        add_to_stat_log(stats, "Passed selection screen check")

        # Pressing A until we're on the yes/no starter select prompt
        t = time.time()
        add_to_stat_log(stats, "Pressing A until starter select hand appears....")
        yes_select_present = False
        while True:
            mses = []
            for i in range(50):
                img_area = relative_crop(get_image(), 0.325, 0.35, 0.35, 0.325)
                mses.append(mse(hand_turtwig, img_area))

            img_mse = np.min(mses)
            add_to_stat_log(stats, f"Hand Select MSE: {img_mse}")

            if img_mse < 30:
                yes_select_present = True
                break

            press_button(nx, controller_index, "A", duration=2.0)

            if time.time() - t > 30:
                break

        if yes_select_present is False:
            add_to_stat_log(stats, "Something went wrong. Hand not seen in time.")
            exit_and_reset(nx, controller_index, stats)
            continue

        # Pressing A until we're on the yes/no starter select prompt
        t = time.time()
        add_to_stat_log(stats, "Moving right until hand selects the chosen starter...")
        yes_select_present = False
        while True:
            mses = []
            for i in range(50):
                img = get_image()
                height, width, _ = img.shape
                if pokemon == CHIMCHAR:
                    xl = 0.46
                    xr = 0.48
                    yb = 0.5
                    yt = 0.46
                elif pokemon == PIPLUP:
                    xl = 0.65
                    xr = 0.67
                    yb = 0.35
                    yt = 0.325
                else:
                    xl = 0.325
                    xr = 0.35
                    yb = 0.35
                    yt = 0.325
                img_area = relative_crop(img, xl, xr, yb, yt)

                if pokemon == CHIMCHAR:
                    mses.append(mse(hand_chimchar, img_area))
                elif pokemon == PIPLUP:
                    mses.append(mse(hand_piplup, img_area))
                else:
                    mses.append(mse(hand_turtwig, img_area))

            img_mse = np.min(mses)
            add_to_stat_log(stats, f"Hand Select MSE: {img_mse}")

            if img_mse < 30:
                yes_select_present = True
                break

            press_button(nx, controller_index, "DPAD_RIGHT")
            time.sleep(0.75)

            if time.time() - t > 30:
                break

        if yes_select_present is False:
            add_to_stat_log(stats, "Something went wrong. Hand not selected in time.")
            exit_and_reset(nx, controller_index, stats)
            continue

        # Pressing A until we're on the yes/no starter select prompt
        t = time.time()
        add_to_stat_log(stats, "Pressing A until starter yes/no selection...")
        yes_select_present = False
        while True:
            img = relative_crop(get_image(), 0.8, 0.825, 0.75, 0.675)
            img_mse = mse(yes_select_check, img)
            add_to_stat_log(stats, f"Yes Select MSE: {img_mse}")

            if img_mse < 15:
                yes_select_present = True
                break

            press_button(nx, controller_index, "A", duration=2.0)

            if time.time() - t > 30:
                break

        if yes_select_present is False:
            add_to_stat_log(stats, "Something went wrong. Starter not selected in time.")
            exit_and_reset(nx, controller_index, stats)
            continue

        # Select yes and check the selection
        add_to_stat_log(stats, "Starter present. Selecting...")
        for i in range(3):
            tilt_stick(nx, controller_index, "L_STICK", 0, 100, duration=0.2)
        time.sleep(1)
        press_button(nx, controller_index, "A")
        press_button(nx, controller_index, "A")
        add_to_stat_log(stats, "Starter selected")
        
        wait_for_battle(get_image)
        add_to_stat_log(stats, "Battle detected")

        t = time.time()
        result = detect_shiny_starter(get_image)
        add_to_stat_log(stats, f"HP Bar Time: {time.time() - t}")

        if result:
            add_to_stat_log(stats, "Shiny detected")
            return True
        else:
            add_to_stat_log(stats, "Shiny not detected")

        # Shiny not detected. Resetting.
        press_button(nx, controller_index, "HOME")
        time.sleep(2.5)

        # Checking if we're on the home menu
        hm_check = relative_crop(get_image(), 0.0, 0.05, 0.8, 0.7)
        hm_mean = hm_check.transpose(2,0,1).mean(axis=(1,2))
        
        add_to_stat_log(stats, "Checking if we're on the home menu...")
        if abs(hm_mean[0] - 55) < 2 and abs(hm_mean[1] - 55) < 2 and abs(hm_mean[2] - 55) < 2:
            add_to_stat_log(stats, "On home menu")
        else:
            add_to_stat_log(stats, "Not on home menu. Attempting to exit to home menu...")
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
        
        press_button(nx, controller_index, "X")
        time.sleep(0.75)
        press_button(nx, controller_index, "A")
        time.sleep(3)

        stats['reset_count'] += 1
        with open("stats.json", "w") as f:
            json.dump(stats, f)


if __name__ == "__main__":
    reset_hunt()
    send_message("Found a shiny")
