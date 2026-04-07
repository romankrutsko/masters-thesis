import pandas as pd
import statsmodels.formula.api as smf
import matplotlib.pyplot as plt

auto = pd.read_csv("data/csv/Auto.csv", header=0, na_values="?")
auto = auto.dropna()

model1 = smf.ols("mpg ~ horsepower", data=auto).fit()

plt.scatter(auto["horsepower"], auto["mpg"])
x_vals = auto["horsepower"].sort_values()
y_vals = model1.predict(pd.DataFrame({"horsepower": x_vals}))
plt.plot(x_vals, y_vals, linewidth=3, color="red")
plt.xlabel("horsepower")
plt.ylabel("mpg")
plt.show()