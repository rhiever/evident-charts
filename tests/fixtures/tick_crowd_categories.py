from _clean import new

# Sixteen categories on a short canvas: their y tick labels nearly touch.
fig, ax = new("Store P sold the most units", figsize=(6, 3.2))
names = [f"Store {c}" for c in "ABCDEFGHIJKLMNOP"]
ax.barh(names, range(1, 17), color="C0")
ax.tick_params(labelsize=9.5)
ax.set_xlabel("Units sold (k)")
fig.subplots_adjust(bottom=0.2, left=0.2)
fig.savefig("out.png")
