from _clean import new

fig, ax = new("Norway produces the most per hour")
x = [1400, 1470, 1600, 1750, 1900, 1900]
y = [134, 120, 90, 70, 50, 36]
ax.scatter(x, y, s=60, color="0.3")
# "Norway" is anchored on Norway's dot but pushed right until it sits next to
# Denmark's dot: a reader pairs it with the wrong country.
ax.annotate("Norway", xy=(1400, 134), xytext=(42, -18), textcoords="offset points",
            ha="left", va="center", fontsize=12)
# Free text right of two stacked dots, halfway between them: equally near both.
ax.text(1915, 43, "Chile", va="center", fontsize=12)
ax.set_xlim(1300, 2000)
ax.set_ylim(0, 160)
ax.set_xlabel("Hours worked per year")
ax.set_ylabel("GDP per hour ($)")
fig.savefig("out.png")
