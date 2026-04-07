import pandas as pd
import matplotlib.pyplot as plt

college = pd.read_csv("data/csv/College.csv", header=0)
college.index = college.iloc[:, 0]
college = college.iloc[:, 1:]

Elite = pd.Series("No", index=college.index)
Elite[college["Top10perc"] > 50] = "Yes"
college["Elite"] = pd.Categorical(Elite)

plt.figure()
college.boxplot(column="Outstate", by="Elite")
plt.xlabel("Elite")
plt.ylabel("Out-of-state tuition")
plt.title("")
plt.suptitle("")

fig, axes = plt.subplots(2, 2)
axes[0, 0].hist(college["Apps"], bins=50)
axes[0, 0].set_title("# of applications")

axes[0, 1].hist(college["Enroll"], bins=25)
axes[0, 1].set_title("# of new enrollment")

axes[1, 0].hist(college["Expend"], bins=10)
axes[1, 0].set_title("Instructional expenditure per student")

axes[1, 1].hist(college["Outstate"])
axes[1, 1].set_title("Out-of-state tuition")

plt.tight_layout()
plt.show()