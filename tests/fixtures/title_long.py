from _clean import new

titles = [
    "Revenue doubled after the 2020 launch,\nled by online sales,\nwhile stores held flat",
    "Revenue doubled after the 2020 launch of the online store and the new app\nwhile in-person sales barely moved at all across the forty stores",
    "Revenue doubled after the 2020 launch of the new online checkout and the delivery app",  # fits blog, not mobile
    "Revenue doubled after the 2020 launch of the online store, the new app, and the loyalty program, while "
    "in-person sales at the forty stores barely moved and the catalog business kept shrinking every single year",
]
for i, title in enumerate(titles):
    fig, ax = new(title)
    ax.plot([2019, 2020, 2021, 2022], [10, 12, 19, 24], color="C0", lw=2)
    ax.set_ylabel("Revenue ($M)")
    fig.text(0.02, 0.02, "Source: Acme Corp., annual reports", fontsize=11)
    fig.savefig(f"out{i}.png")
