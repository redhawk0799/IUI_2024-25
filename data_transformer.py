import socket
import struct

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