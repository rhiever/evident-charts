import matplotlib.pyplot as plt

from _clean import clean, new

figs = []


def chart(title="Germany leads on wind", **kw):
    fig, ax = new(title, **kw)
    figs.append(fig)
    return ax


# Sorted, with Other kept last.
ax = chart()
ax.barh(["Other", "Sweden", "Poland", "Spain", "Italy", "Germany"], [90, 10, 38, 47, 59, 82], color="C0")
# Gainers, then losers by size of loss.
ax = chart()
ax.barh(["Oslo", "Lima", "Pune", "Kyiv", "Rome", "Nice"][::-1], [8, 5, 2, -6, -3, -1][::-1], color="C0")
# Sections under header rows, each sorted on its own.
ax = chart()
rows = ["Europe", "Germany", "France", "Spain", "Asia", "Japan", "India", "Korea"]
vals = {"Germany": 82, "France": 40, "Spain": 30, "Japan": 90, "India": 60, "Korea": 20}
pos = [k for k, r in enumerate(rows) if r in vals]
ax.barh(pos, [vals[rows[k]] for k in pos], color="C0")
ax.set_yticks(range(len(rows)), rows)
ax.invert_yaxis()
# Near-ties (82.3, 82.1, 82.4) are not order errors.
ax = chart()
ax.barh(["Japan", "Spain", "Italy", "France", "Chile"][::-1], [82.3, 82.1, 82.4, 70, 60][::-1], color="C0")
# Natural order: months, age bands, Likert levels, month initials.
ax = chart("Sales peaked in February")
ax.bar(["Jan", "Feb", "Mar", "Apr", "May"], [4, 8, 5, 7, 3], color="C0")
ax = chart("Adults 25-34 use it most")
ax.bar(["18-24", "25-34", "35-44", "45-54", "55-64", "65+"], [40, 82, 59, 47, 38, 10], color="C0")
ax = chart("Most agree")
ax.plot(["Strongly disagree", "Disagree", "Neutral", "Agree", "Strongly agree"], [5, 12, 20, 40, 23], marker="o")
ax = chart("Sales peaked in February")
ax.bar(list("JFMAM"), [4, 8, 5, 7, 3], color="C0")
# Years as numbers keep their true spacing.
ax = chart("Output peaked in 2012")
ax.bar([2010, 2012, 2015, 2016, 2020], [4, 8, 5, 7, 3], color="C0")
# Floating waterfall steps follow the calculation, not the values.
ax = chart("Costs ate half of revenue")
ax.bar(["Revenue", "Materials", "Labor", "Profit"], [10, -3, -2, 5], bottom=[0, 10, 7, 0], color="C0")
# The right panel shares rows with the sorted left panel.
fig, (left, right) = plt.subplots(1, 2, sharey=True, figsize=(8, 5))
figs.append(fig)
fig.suptitle("Germany leads on wind and solar")
names = ["Sweden", "Poland", "Spain", "Italy", "Germany"]
left.barh(names, [10, 38, 47, 59, 82], color="C0")
right.barh(names, [5, 20, 18, 30, 60][::-1], color="C0")
# Separate panels keep one row order.
fig, (left, right) = plt.subplots(1, 2, figsize=(8, 5))
figs.append(fig)
fig.suptitle("Germany leads on wind and solar")
left.barh(names, [10, 38, 47, 59, 82], color="C0")
right.barh(names, [5, 20, 18, 30, 60][::-1], color="C0")
for f in figs:
    for a in f.axes:
        clean(a)
    f.savefig("out.png")
