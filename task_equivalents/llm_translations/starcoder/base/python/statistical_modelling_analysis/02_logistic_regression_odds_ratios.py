import pandas as pd

Weekly = pd.read_csv('data/csv/Weekly.csv', index_col=0)
x01 = Weekly.iloc[:, 2:8]
y01 = (Weekly['Direction'] == 'Up').astype(int)

from sklearn.linear_model import LogisticRegression
log_reg = LogisticRegression()
log_reg.fit(x01, y01)
print(log_reg.coef_)
print(log_reg.intercept_)

prob = log_reg.predict_proba(x01)[:, 1]
pred = (prob > .5).astype(int)
print((y01 == pred).mean())