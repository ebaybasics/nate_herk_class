import sys
import json
import base64
import io
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def generate_chart(chart_data: dict) -> str:
    labels = chart_data["labels"]
    values = chart_data["values"]
    title = chart_data.get("title", "")

    fig, ax = plt.subplots(figsize=(6, max(2.0, len(labels) * 0.65)))
    colors = ["#6366f1", "#8b5cf6", "#a78bfa", "#c4b5fd", "#ddd6fe"]
    ax.barh(labels, values, color=colors[: len(labels)], height=0.5)
    ax.set_title(title, fontsize=11, fontweight="bold", pad=10)
    for spine in ["top", "right", "left"]:
        ax.spines[spine].set_visible(False)
    ax.tick_params(labelsize=9)
    ax.set_facecolor("white")
    fig.patch.set_facecolor("white")
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


if __name__ == "__main__":
    data = json.loads(sys.stdin.read())
    print(generate_chart(data))
