from _clean import new

# Nominal bars in dataframe order.
fig, ax = new("Germany leads on wind")
ax.barh(["France", "Germany", "Italy", "Spain", "Poland", "Sweden"], [40, 82, 59, 47, 38, 10], color="C0")
ax.set_xlabel("Capacity (GW)")
# Alphabetical columns.
fig1, ax1 = new("Mangoes cost the most")
ax1.bar(["Apples", "Bananas", "Cherries", "Mangoes", "Pears"], [3, 1, 6, 8, 2], color="C0")
ax1.set_ylabel("Price ($/kg)")
# A line joining nominal categories.
fig2, ax2 = new("South sells the most")
ax2.plot(["North", "South", "East", "West"], [4, 8, 5, 7], color="C0", marker="o")
ax2.set_ylabel("Sales ($M)")
# Years as strings: 2010, 2012, 2015, 2016, 2020 drawn evenly spaced.
fig3, ax3 = new("Output peaked in 2012")
ax3.bar(["2010", "2012", "2015", "2016", "2020"], [4, 8, 5, 7, 3], color="C0")
ax3.set_ylabel("Output (Mt)")
for i, f in enumerate([fig, fig1, fig2, fig3]):
    f.savefig(f"{i}.png")
