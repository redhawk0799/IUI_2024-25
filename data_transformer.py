import socket
import struct
import pandas as pd
import numpy as np
import time

from teslasuit_sdk import ts_api
import teslasuit_sdk.subsystems.ts_haptic
from teslasuit_sdk.ts_mapper import TsBone2dIndex
import config_tesla

# Define the IP and port to listen on
LISTEN_IP = "127.0.0.1"  # Listen on all available interfaces
LISTEN_PORT = 27152  # Replace with the port your server is sending data to

# Teslasuit stuff
areas = {
    "LeftFrontThigh": 0,
    "LeftBackThigh": 1,
    "RightFrontThigh": 2,
    "RightBackThigh": 3,
    "LeftFrontLowerLeg": 4,
    "LeftBackLowerLeg": 5,
    "RightFrontLowerLeg": 6,
    "RightBackLowerLeg": 7,
    "Abdominal": 8,
    "UpperChest": 9,
    "Back": 11,
    "LeftFrontUpperArm": 12,
    "LeftBackUpperArm": 13,
    "RightFrontUpperArm": 14,
    "RightBackUpperArm": 15,
    "LeftFrontLowerArm": 16,
    "LeftBackLowerArm": 17,
    "RightFrontLowerArm": 18,
    "RightBackLowerArm": 19
}


def start_udp_listener():
    #print("Initialize API")
    #api = ts_api.TsApi()

    #device = api.get_device_manager().get_or_wait_last_device_attached()
    #player = device.haptic
    #mapper = api.mapper

    #print("Setup channels to play and touch parameters")
    #layout = mapper.get_haptic_electric_channel_layout(device.get_mapping())
    #bones = mapper.get_layout_bones(layout)



    # Create a UDP socket
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Bind the socket to the specified IP and port
    udp_socket.bind((LISTEN_IP, LISTEN_PORT))

    print(f"Listening for UDP data on {LISTEN_IP}:{LISTEN_PORT}...")

    csv_data = pd.read_csv('./actual_data.csv', usecols=['currentTime', 'world_position_x', 'world_position_y', 'speed'])

    start_time = csv_data.iloc[0]['currentTime']
    list_with_interval = []
    split_data = []

    for _, row in csv_data.iterrows():
        if row['currentTime'] - start_time <= 0.25:
            list_with_interval.append(row.tolist())
        else:
            split_data.append(list_with_interval)
            list_with_interval = [row.tolist()]
            start_time = row['currentTime']

    if list_with_interval:
        split_data.append(list_with_interval)

    average_x_data = []
    average_y_data = []
    average_speed_data = []

    for data in split_data:
        numpy_array = np.array(data)
        x_values = numpy_array[:, 1]
        y_values = numpy_array[:, 2]
        speed_vals = numpy_array[:, 3]
        average_speed = speed_vals.mean()
        average_x = x_values.mean()
        average_y = y_values.mean()

        average_x_data.append(round(average_x.tolist(), 3))
        average_y_data.append(round(average_y.tolist(), 3))
        average_speed_data.append(round(average_speed.tolist(), 3))

    all_coordinates = list(zip(average_speed_data, average_y_data, average_x_data)) # this groups the data as a list of coordinates

    array_for_interval = []
    start_time = time.time()
    reached_start = False
    old_mean_array_of_incoming = []

    try:
        while True:
            # Receive data from the sender
            data, addr = udp_socket.recvfrom(16)
            format = "ffff"
            our_data = struct.unpack(format, data)

            normalized_data = [round(our_data[0], 3), round(our_data[2], 3), round(our_data[1], 3), round(our_data[3], 3)]

            array_for_interval.append(normalized_data)
            if time.time() <= start_time + 0.25:
                continue


            # clear the first coordinate to look ahead


            mean_data_of_incoming = np.array(array_for_interval)
            mean_array_of_incoming = [round(mean_data_of_incoming[:, 1].mean(), 3), round(mean_data_of_incoming[:, 0].mean(), 3),  round(mean_data_of_incoming[:, 3].mean(), 3)]
            if not old_mean_array_of_incoming:
                old_mean_array_of_incoming = mean_array_of_incoming


            if not reached_start:
                if all_coordinates[0][0] - 5 < mean_array_of_incoming[0] < all_coordinates[0][0] + 5 and all_coordinates[0][1] - 5 < mean_array_of_incoming[1] < all_coordinates[0][1] + 5:
                    reached_start = True
                else:
                    if old_mean_array_of_incoming != mean_array_of_incoming:
                        old_mean_array_of_incoming = mean_array_of_incoming
                        print("Please go to start point:", all_coordinates[0])
                        print("You are at:", mean_array_of_incoming[0], mean_array_of_incoming[1])

            if reached_start:
                all_coordinates = all_coordinates[1:]

                signal = []
                # check for x
                if not all_coordinates[0][0] - 5 < mean_array_of_incoming[0] < all_coordinates[0][0] + 5: # [-1187.798, 640.779, 0.01]
                    print(f'X is wrong. IST {mean_array_of_incoming[0]} SOLL {all_coordinates[0][0]}')
                    signal = [["LeftFrontUpperArm", "LeftFrontLowerArm", "LeftBackUpperArm", "LeftBackLowerArm"], 80, 500]
                if not all_coordinates[0][1] - 5 < mean_array_of_incoming[1] < all_coordinates[0][1] + 5:
                    print(f'Y is wrong. IST {mean_array_of_incoming[1]} SOLL {all_coordinates[0][1]}')
                    signal = [["RightFrontUpperArm", "RightFrontLowerArm", "RightBackUpperArm", "RightBackLowerArm"], 80, 500]

                if not all_coordinates[0][2] - 5 < mean_array_of_incoming[2]:
                    print(f'too slow. IST {mean_array_of_incoming[2]} SOLL {all_coordinates[0][2]}')
                    signal = ["RightFrontLowerLeg", 80, 500]
                if not mean_array_of_incoming[2] < all_coordinates[0][2] + 5:
                    print(f'too fast. IST {mean_array_of_incoming[2]} SOLL {all_coordinates[0][2]}')
                    signal = ["LeftFrontLowerLeg", 80, 500]

                if len(signal) <= 0:
                    continue

                #channels = mapper.get_bone_contents(bones[areas[signal[0]]])
                #params = player.create_touch_parameters(100, 40, signal[1])
                #playable_id = player.create_touch(params, channels, signal[2])
                #player.play_playable(playable_id)

                # reset the used array and get the new time
            array_for_interval = []
            start_time = time.time()

    except KeyboardInterrupt:
        print("Stopping UDP listener.")
    finally:
        udp_socket.close()

if __name__ == "__main__":
    start_udp_listener()