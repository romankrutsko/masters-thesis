import random
import pandas as pd

college = pd.read_csv("data/csv/College.csv")

college.index = college.iloc[:, 0]
college = college.iloc[:, 1:].copy()

college["Private01"] = (college["Private"] == "Yes").astype(int)
college = college.drop(columns=["Private"])

x = college.drop(columns=["Apps"]).apply(pd.to_numeric)
y = college["Apps"]

random.seed(1)
train = random.sample(range(len(college)), len(college) // 2)
test = sorted(set(range(len(college))) - set(train))

xtrain = x.iloc[train]
xtest = x.iloc[test]
ytrain = y.iloc[train]
ytest = y.iloc[test]