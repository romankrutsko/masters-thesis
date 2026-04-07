import numpy as np
import pandas as pd
from patsy import dmatrices

College = pd.read_csv("data/csv/College.csv", header=0)
College.index = College.iloc[:, 0]
College = College.iloc[:, 1:]

np.random.seed(1)
train = np.random.choice(College.index, size=len(College) // 2, replace=False)
test = College.index.difference(train)

df_train = College.loc[train, :]
df_test = College.loc[test, :]

y_train, x_train = dmatrices("Apps ~ .", data=df_train, return_type="dataframe")
y_train = y_train.iloc[:, 0]
x_train = x_train.iloc[:, 1:]

y_test, x_test = dmatrices("Apps ~ .", data=df_test, return_type="dataframe")
y_test = y_test.iloc[:, 0]
x_test = x_test.iloc[:, 1:]