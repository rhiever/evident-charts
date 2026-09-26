from matplotlib.figure import Figure

fig = Figure(figsize=(6, 4))
ax = fig.add_subplot()
ax.text(0.5, 0.5, "Overlapping", fontsize=12)
ax.text(0.52, 0.5, "Overlapping", fontsize=12, color="red")
