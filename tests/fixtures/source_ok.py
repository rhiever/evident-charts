from _clean import new

# Reader-facing notes: past tenses like "confirmed" are not process notes, and a domain is not a file.
fig, ax = new("Confirmed cases peaked in January")
ax.plot([2021, 2022, 2023, 2024], [10, 24, 12, 8], color="C0", lw=2)
ax.set_xticks([2021, 2022, 2023, 2024])
ax.set_ylabel("Confirmed cases (k)")
fig.subplots_adjust(bottom=0.2)
fig.text(0.02, 0.02, "Note: 2024 is provisional.\nSource: CDC, National Notifiable Diseases Surveillance System",
         fontsize=11)
fig.text(0.98, 0.02, "Dr. Jane Doe | janedoe.com", fontsize=11, ha="right")
# "Data:" also opens a source line.
fig2, ax2 = new("Confirmed cases peaked in January")
ax2.plot([2021, 2022, 2023, 2024], [10, 24, 12, 8], color="C0", lw=2)
ax2.set_xticks([2021, 2022, 2023, 2024])
ax2.set_ylabel("Confirmed cases (k)")
fig2.text(0.02, 0.02, "Chart: Jane Doe | Data: CDC NNDSS", fontsize=11)
# "Source:" mid-line, after a note, also counts.
fig3, ax3 = new("Confirmed cases peaked in January")
ax3.plot([2021, 2022, 2023, 2024], [10, 24, 12, 8], color="C0", lw=2)
ax3.set_xticks([2021, 2022, 2023, 2024])
ax3.set_ylabel("Confirmed cases (k)")
fig3.text(0.02, 0.02, "Note: 2024 is provisional. Source: CDC NNDSS", fontsize=11)
fig.savefig("a.png")
fig2.savefig("b.png")
fig3.savefig("c.png")
