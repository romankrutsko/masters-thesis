import pandas as pd
import matplotlib.pyplot as plt

college = pd.read_csv("data/csv/College.csv")

college.index = college.iloc[:, 0]
college = college.iloc[:, 1:].copy()

college["Elite"] = pd.Categorical(
    pd.Series("No", index=college.index).where(college["Top10perc"] <= 50, "Yes")
)

plt.figure()
plt.boxplot(
    [
        college.loc[college["Elite"] == "No", "Outstate"],
        college.loc[college["Elite"] == "Yes", "Outstate"],
    ],
    tick_labels=["No", "Yes"],
)
plt.xlabel("Elite")
plt.ylabel("Out-of-state tuition")

fig, axes = plt.subplots(2, 2)
axes[0, 0].hist(college["Apps"], bins=50)
axes[0, 0].set_xlabel("new applications")
axes[0, 0].set_title("")

axes[0, 1].hist(college["Enroll"], bins=45)
axes[0, 1].set_xlabel("new enrollment")
axes[0, 1].set_title("")

axes[1, 0].hist(college["Expend"], bins=30)
axes[1, 0].set_xlabel("Instructional expenditure per student")
axes[1, 0].set_title("")

axes[1, 1].hist(college["Outstate"])
axes[1, 1].set_xlabel("Out-of-state tuition")
axes[1, 1].set_title("")

plt.tight_layout()
plt.show()