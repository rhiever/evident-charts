import matplotlib.pyplot as plt
fig, ax = plt.subplots()
ax.plot([1, 2], [1, 2])
fig.savefig("SHOULD_NOT_EXIST.png")
print("saved chart")
