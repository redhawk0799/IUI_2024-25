import threading
import time
import tkinter as tk

class SuitSimulator:
    def __init__(self):
        # Mapping areas to their positions on the simulated suit
        self.areas = {
            "LeftLowerArm": (70, 50, 100, 50),
            "LeftUpperArm": (20, 50, 100, 50),

            "RightUpperArm": (300, 50, 100, 50),
            "RightLowerArm": (330, 50, 100, 50),

            "LeftThigh": (150, 200, 50, 100),
            "RightThigh": (250, 200, 50, 100),

            "LeftLowerLeg": (150, 300, 50, 100),
            "RightLowerLeg": (250, 300, 50, 100),

            "Abdominal": (150, 150, 150, 50),
            "UpperChest": (150, 50, 150, 50),
            "Back": (150, 50, 150, 50),
        }

        self.current_highlights = []  # Areas to highlight
        self.lock = threading.Lock()

        # Set up the GUI window
        self.root = tk.Tk()
        self.root.title("Suit Simulator")
        self.canvas = tk.Canvas(self.root, width=500, height=400, bg="white")
        self.canvas.pack()

        # Draw static suit areas
        self.rectangles = {}
        for area, (x, y, w, h) in self.areas.items():
            rect = self.canvas.create_rectangle(
                x, y, x + w, y + h, fill="lightgray", outline="black"
            )
            self.rectangles[area] = rect
            self.canvas.create_text(
                x + w / 2, y + h / 2, text=area, font=("Arial", 8), fill="black"
            )

    def highlight_areas(self, areas):
        """Highlight specified areas on the suit."""
        with self.lock:
            self.current_highlights = areas

        # Update the highlighted areas
        for area, rect in self.rectangles.items():
            color = "red" if area in areas else "lightgray"
            self.canvas.itemconfig(rect, fill=color)

    def update_display(self):
        """Periodically update the display based on feedback."""
        while True:
            with self.lock:
                areas_to_highlight = self.current_highlights
            self.highlight_areas(areas_to_highlight)
            time.sleep(0.1)

    def run(self):
        """Run the simulator."""
        update_thread = threading.Thread(target=self.update_display, daemon=True)
        update_thread.start()
        self.root.mainloop()

#
# if __name__ == "__main__":
#     simulator = SuitSimulator()  # Initialize the simulator
#
#     def run_haptic_system():
#         system = HapticFeedbackSystem(simulator)
#         system.start()
#
#     # Run the HapticFeedbackSystem in a separate thread
#     haptic_thread = threading.Thread(target=run_haptic_system)
#     haptic_thread.start()
#
#     # Run the simulator in the main thread
#     simulator.run()
