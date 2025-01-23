import socket
import struct
import pandas as pd
import numpy as np

from teslasuit_sdk import ts_api
import teslasuit_sdk.subsystems.ts_haptic
from teslasuit_sdk.ts_mapper import TsBone2dIndex
import config_tesla

connect = False

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
    # Create a UDP socket
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Bind the socket to the specified IP and port
    udp_socket.bind((LISTEN_IP, LISTEN_PORT))

    print(f"Listening for UDP data on {LISTEN_IP}:{LISTEN_PORT}...")

    csv_data = pd.read_csv('./dummy_data.csv', usecols=['currentTime', 'world_position_x', 'world_position_y'])

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

    for data in split_data:
        numpy_array = np.array(data)
        x_values = numpy_array[:, 1]
        y_values = numpy_array[:, 2]
        average_x = x_values.mean()
        average_y = y_values.mean()

        average_x_data.append(round(average_x.tolist(), 3))
        average_y_data.append(round(average_y.tolist(), 3))

    all_coordinates = list(zip(average_x_data, average_y_data)) # this groups the data as a list of coordinates

    print(f"coordinates: {all_coordinates}")
    return

    try:
        while True:
            # Receive data from the sender
            data, addr = udp_socket.recvfrom(16)  # Buffer size of 1024 bytes
            format = "ffff"
            our_data = struct.unpack(format, data)

            normalized_data = {
                "x_cor" : round(our_data[0], 3),
                "y_cor" : round(our_data[1], 3),
                "z_cor" : round(our_data[2], 3),
                "speed" : round(our_data[3], 3)
            }

            print(f"Data: {normalized_data}")

    except KeyboardInterrupt:
        print("Stopping UDP listener.")
    finally:
        udp_socket.close()

def connectToSuit():
    location = ['Pectoral_L', 'Tricep_L', 'Shoulder_L', 'Bicep_L',
                'BackUp_L', 'BackDown_L', 'Pectoral_R', 'Tricep_R', 'Shoulder_R',
                'Bicep_R', 'BackUp_R', 'BackDown_R']

    print("Initialize API")
    api = ts_api.TsApi()

    device = api.get_device_manager().get_or_wait_last_device_attached()
    player = device.haptic
    mapper = api.mapper

    print("Setup channels to play and touch parameters")
    layout = mapper.get_haptic_electric_channel_layout(device.get_mapping())
    bones = mapper.get_layout_bones(layout)

    signal = []

    channels = mapper.get_bone_contents(bones[areas[signal[0]]])
    params = player.create_touch_parameters(100, 40, signal[1])
    playable_id = player.create_touch(params, channels, signal[2])
    player.play_playable(playable_id)

if __name__ == "__main__":
    if connect:
        connectToSuit()

    start_udp_listener()