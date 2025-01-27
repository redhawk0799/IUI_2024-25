import threading
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
LISTEN_IP = "127.0.0.1"
LISTEN_PORT = 27152

# Teslasuit areas
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

class HapticFeedbackSystem:
    def __init__(self, simulator):
        self.simulator = simulator
        self.running = True
        self.data_lock = threading.Lock()
        self.shared_data = {
            "incoming_data": [],
            "mean_data": None,
            "reached_start": False
        }
        self.csv_data = pd.read_csv('./actual_data.csv', usecols=['currentTime', 'world_position_x', 'world_position_y', 'speed'])
        self.all_coordinates = self.preprocess_csv_data(self.csv_data)
        self.last_feedback_time = 0
        self.feedback_interval = 0.25

    def preprocess_csv_data(self, csv_data):
        """Preprocess CSV data to group by 0.25-second intervals."""
        start_time = csv_data.iloc[0]['currentTime']
        list_with_interval = []
        split_data = []

        csv_data["speed"] = csv_data["speed"] * 2.60934

        for _, row in csv_data.iterrows():
            if row['currentTime'] - start_time <= 0.25:
                list_with_interval.append(row.tolist())
            else:
                split_data.append(list_with_interval)
                list_with_interval = [row.tolist()]
                start_time = row['currentTime']

        if list_with_interval:
            split_data.append(list_with_interval)

        average_data = [
            (round(np.array(data)[:, 3].mean(), 3),  # speed
             round(np.array(data)[:, 2].mean(), 3),  # y
             round(np.array(data)[:, 1].mean(), 3))  # x
            for data in split_data
        ]
        return average_data

    def udp_listener(self):
        """Thread to listen for UDP data."""
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.bind((LISTEN_IP, LISTEN_PORT))
        print(f"Listening for UDP data on {LISTEN_IP}:{LISTEN_PORT}...")
        array_for_interval = []
        start_time = time.time()

        try:
            while self.running:
                data, addr = udp_socket.recvfrom(16)
                format = "ffff"
                our_data = struct.unpack(format, data)
                normalized_data = [round(our_data[0], 3), round(our_data[2], 3), round(our_data[1], 3), round(our_data[3], 3)]
                array_for_interval.append(normalized_data)

                if time.time() <= start_time + 0.25:
                    continue

                mean_data_of_incoming = np.array(array_for_interval)
                mean_array_of_incoming = [
                    round(mean_data_of_incoming[:, 1].mean(), 3),
                    round(mean_data_of_incoming[:, 0].mean(), 3),
                    round(mean_data_of_incoming[:, 3].mean(), 3)
                ]

                with self.data_lock:
                    self.shared_data["incoming_data"] = array_for_interval
                    self.shared_data["mean_data"] = mean_array_of_incoming

                array_for_interval = []
                start_time = time.time()

        except KeyboardInterrupt:
            print("Stopping UDP listener.")
        finally:
            udp_socket.close()

    def calculate_thresholds(self, current_position, speed, context):
        """Calculate thresholds with additional contextual adjustments."""
        base_threshold = 7
        speed_factor = max(1 - (speed / 100), 0.5)
        context_factor = {
            "corner": 0.8,
            "straight": 1.2
        }.get(context, 1.0)

        dynamic_threshold_x = base_threshold * speed_factor * context_factor
        dynamic_threshold_y = base_threshold * speed_factor * context_factor
        dynamic_threshold_speed = base_threshold * 0.5  # Example: fixed scaling for speed

        return dynamic_threshold_x, dynamic_threshold_y, dynamic_threshold_speed

    def feedback_processor(self):
        """Thread to process feedback and send haptic signals."""
        old_mean_array_of_incoming = []

        while self.running:
            with self.data_lock:
                mean_array_of_incoming = self.shared_data.get("mean_data", None)

            if mean_array_of_incoming is None:
                time.sleep(0.05)
                continue

            if not old_mean_array_of_incoming:
                old_mean_array_of_incoming = mean_array_of_incoming

            if not self.shared_data.get("reached_start"):
                if self.check_start(mean_array_of_incoming):
                    with self.data_lock:
                        self.shared_data["reached_start"] = True
                else:
                    if (abs(mean_array_of_incoming[0] - old_mean_array_of_incoming[0]) > 0.1 or
                            abs(mean_array_of_incoming[1] - old_mean_array_of_incoming[1]) > 0.1):
                        print("Please go to start point:", self.all_coordinates[0])
                        print("You are at:", mean_array_of_incoming[0], mean_array_of_incoming[1])
                    old_mean_array_of_incoming = mean_array_of_incoming
                    continue

            # Process feedback
            # self.all_coordinates = self.all_coordinates[1:] if self.all_coordinates else self.all_coordinates
            # self.send_haptic_feedback(mean_array_of_incoming)
            closest_idx = self.find_closest_position(mean_array_of_incoming)
            if closest_idx + 1 < len(self.all_coordinates):
                target_coord = self.all_coordinates[closest_idx + 1]
            else:
                target_coord = self.all_coordinates[closest_idx]  # Default to the closest if no next exists

            if closest_idx - 1 >= 0:
                prev_coord = self.all_coordinates[closest_idx - 1]
            else:
                prev_coord = self.all_coordinates[closest_idx]

            optimal_vector = np.array([
                target_coord[0] - prev_coord[0],
                target_coord[1] - prev_coord[1]
            ])

            current_vector = np.array([
                target_coord[0] - mean_array_of_incoming[0],
                target_coord[1] - mean_array_of_incoming[1]
            ])

            self.send_haptic_feedback(mean_array_of_incoming, target_coord, optimal_vector, current_vector)

    def find_closest_position(self, current_position):
        """Find the index of the closest position in all_coordinates."""
        distances = [
            np.sqrt(
                (coord[0] - current_position[0]) ** 2 +
                (coord[1] - current_position[1]) ** 2 +
                (coord[2] - current_position[2]) ** 2
            )
            for coord in self.all_coordinates
        ]
        closest_idx = np.argmin(distances)
        return closest_idx


    def check_start(self, mean_array_of_incoming):
        """Check if the player has reached the starting point."""
        coord = self.all_coordinates[0]
        return all([
            coord[0] - 5 < mean_array_of_incoming[0] < coord[0] + 5,
            coord[1] - 5 < mean_array_of_incoming[1] < coord[1] + 5
        ])

    def send_haptic_feedback(self, mean_array_of_incoming, target_coord, optimal_vector, current_vector):
        """Send haptic feedback based on deviations."""
        current_time = time.time()

        if current_time - self.last_feedback_time < self.feedback_interval:
            return

        dynamic_threshold_x, dynamic_threshold_y, dynamic_threshold_speed = self.calculate_thresholds(
            mean_array_of_incoming,
            mean_array_of_incoming[2],  # Speed as an example factor
            "straight")

        if np.linalg.norm(optimal_vector) > 0:
            optimal_vector = optimal_vector / np.linalg.norm(optimal_vector)
        if np.linalg.norm(current_vector) > 0:
            current_vector = current_vector / np.linalg.norm(current_vector)

        dot_product = np.dot(optimal_vector, current_vector)
        angle = np.arccos(np.clip(dot_product, -1.0, 1.0))  # Angle in radians
        angle_degrees = np.degrees(angle)

        cross_product = np.cross(optimal_vector, current_vector)  # Cross product in 2D
        deviation_side = "left" if cross_product > 0 else "right" if cross_product < 0 else "aligned"

        direction_threshold = 10

        signal = []

        if angle_degrees > direction_threshold:
            print(f"Directional deviation detected: {angle_degrees:.2f}° to the {deviation_side}")

            if deviation_side == "left":
                signal = ["LeftUpperArm", "LeftLowerArm"]
            elif deviation_side == "right":
                signal = ["RightUpperArm", "RightLowerArm"]


        # if not target_coord[0] - dynamic_threshold_x < mean_array_of_incoming[0] < target_coord[0] + dynamic_threshold_x:
        #     print(f'X is wrong. IST {mean_array_of_incoming[0]} SOLL {target_coord[0]}')
        #     signal = ["LeftUpperArm", "LeftLowerArm", "RightUpperArm", "RightLowerArm"]
        # if not target_coord[1] - dynamic_threshold_y < mean_array_of_incoming[1] < target_coord[1] + dynamic_threshold_y:
        #     print(f'Y is wrong. IST {mean_array_of_incoming[1]} SOLL {target_coord[1]}')
        #     signal = ["LeftUpperArm", "LeftLowerArm", "RightUpperArm", "RightLowerArm"]
        if mean_array_of_incoming[2] < target_coord[2] - dynamic_threshold_speed:
            print(f'Speed is too slow. IST {mean_array_of_incoming[2]} SOLL {target_coord[2]}')
            signal.append("RightThigh")
            signal.append("RightLowerLeg")
        elif mean_array_of_incoming[2] > target_coord[2] + dynamic_threshold_speed:
            print(f'Speed is too fast. IST {mean_array_of_incoming[2]} SOLL {target_coord[2]}')
            signal.append("LeftThigh")
            signal.append("LeftLowerLeg")


        # Tesla Suit integration can go here
        if signal:
            print(f"Signal sent: {signal}")
            self.simulator.highlight_areas(signal)
            self.last_feedback_time = current_time


    def start(self):
        """Start the system."""
        listener_thread = threading.Thread(target=self.udp_listener)
        processor_thread = threading.Thread(target=self.feedback_processor)

        listener_thread.start()
        processor_thread.start()

        try:
            while True:
                time.sleep(1)  # Keep the main thread alive
        except KeyboardInterrupt:
            self.running = False
            listener_thread.join()
            processor_thread.join()
            print("System stopped.")

if __name__ == "__main__":
    system = HapticFeedbackSystem()
    simulator = SuitSimulator()
    system.start()
