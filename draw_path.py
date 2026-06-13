import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle

def add_box(ax, x, y, size=1.0, color="blue", label=None):
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
    df = pd.read_csv("ros2/path2.csv")

    x = df["x"].values
    y = df["y"].values

    fig, ax = plt.subplots(figsize=(8, 8))

    ax.plot(x, y, "-o", label="Path")

    # ===== OBJECTS =====
    add_box(ax, 1.0, 4.0, size=1.0, color="blue", label="Target object") # path1
    # add_box(ax, -4.33, 0.14, size=1.0, color="gray", label="Target object") # path_cafe
    # add_box(ax, 3.74, 0.65, size=1.0, color="red", label="Red box")
    # add_circle(ax, 3.66, -2.11, radius=0.5, color="purple", label="Circle")

    # ===== STYLE =====
    ax.set_xlabel("X [m]")
    ax.set_ylabel("Y [m]")
    # ax.set_title("Sequence of actions")
    #ax.axis("equal")
    ax.text(0.5, 1.02,
    "Number of actions: 6\nAverage action selection time: 17.50 s",
    transform=ax.transAxes, ha="center", fontsize=9)
    ax.set_xlim(-2, 6)
    ax.set_ylim(-3, 5)
    ax.grid(True)
    ax.legend()

    plt.show()


if __name__ == "__main__":
    main()