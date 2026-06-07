import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle

def add_box(ax, x, y, size=1.0, color="blue", label=None):
    # Gazebo box is centered → convert to bottom-left corner
    half = size / 2.0
    rect = Rectangle(
        (x - half, y - half),
        size,
        size,
        linewidth=2,
        edgecolor=color,
        facecolor=color,
        alpha=0.3,
        label=label
    )
    ax.add_patch(rect)


def add_circle(ax, x, y, radius=0.5, color="purple", label=None):
    circ = Circle(
        (x, y),
        radius,
        linewidth=2,
        edgecolor=color,
        facecolor=color,
        alpha=0.3,
        label=label
    )
    ax.add_patch(circ)


def main():
    # ===== PATH =====
    df = pd.read_csv("ros2/path1.csv")

    x = df["x"].values
    y = df["y"].values

    fig, ax = plt.subplots(figsize=(8, 8))

    ax.plot(x, y, "-o", label="Path")

    ax.scatter(x[0], y[0], c="green", s=80, label="Start")
    ax.scatter(x[-1], y[-1], c="red", s=80, label="End")

    # ===== OBJECTS (Gazebo world) =====

    # Blue box (assume 1m x 1m)
    add_box(ax, 1.0, 4.0, size=1.0, color="blue", label="Blue box")

    # Red box
    add_box(ax, 3.74, 0.65, size=1.0, color="red", label="Red box")

    # Circle object (assume radius 0.5m)
    add_circle(ax, 3.66, -2.11, radius=0.5, color="purple", label="Circle")

    # ===== STYLE =====
    ax.set_xlabel("X [m]")
    ax.set_ylabel("Y [m]")
    ax.set_title("Robot path + Gazebo objects (real size)")
    ax.axis("equal")
    ax.grid(True)
    ax.legend()

    plt.show()


if __name__ == "__main__":
    main()