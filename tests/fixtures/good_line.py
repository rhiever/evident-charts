import matplotlib.pyplot as plt
from _clean import new

fig, ax = new()
years = [2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023]
a = [10, 11, 12, 12, 15, 19, 22, 24]
b = [9, 9, 10, 10, 11, 11, 12, 12]
ax.plot(years, a, color="#1f77b4", lw=2)
ax.plot(years, b, color="#767676", lw=2)
ax.text(2023.15, 24, "Online", va="center", color="#1f77b4", fontsize=12)
ax.text(2023.15, 12, "Stores", va="center", color="#767676", fontsize=12)
ax.set_xlim(2015.5, 2024.5)
ax.set_ylabel("Revenue ($M)", fontsize=12)
ax.tick_params(labelsize=11)
fig.savefig("out.png")
