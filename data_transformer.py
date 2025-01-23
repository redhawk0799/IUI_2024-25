import socket
import struct
import pandas as pd
import numpy as np

from teslasuit_sdk import ts_api
import teslasuit_sdk.subsystems.ts_haptic
from teslasuit_sdk.ts_mapper import TsBone2dIndex

# Define the IP and port to listen on
LISTEN_IP = "127.0.0.1"  # Listen on all available interfaces
LISTEN_PORT = 27152  # Replace with the port your server is sending data to


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

        average_x_data.append(average_x.tolist())
        average_y_data.append(average_y.tolist())

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


if __name__ == "__main__":
    start_udp_listener()