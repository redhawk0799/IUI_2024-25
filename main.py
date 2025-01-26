from dummy_suit import SuitSimulator
from multithreads import HapticFeedbackSystem
import threading

if __name__ == "__main__":
    simulator = SuitSimulator()
    system = HapticFeedbackSystem(simulator)

    # Run the simulator in the main thread
    simulator_thread = threading.Thread(target=system.start, daemon=True)
    simulator_thread.start()

    simulator.run()  # This blocks and runs the Tkinter GUI
