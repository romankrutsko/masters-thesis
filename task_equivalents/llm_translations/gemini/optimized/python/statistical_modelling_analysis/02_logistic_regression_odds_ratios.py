import pandas as pd
import statsmodels.api as sm

Weekly = pd.read_csv('data/csv/Weekly.csv', index_col=0)

# R's 1-based, inclusive 3:8 maps to Python's 0-based, exclusive 2:8
x01 = Weekly.iloc[:, 2:8]
y01 = (Weekly['Direction'] == 'Up').astype(int)

# Add intercept for statsmodels
X = sm.add_constant(x01)

# Fit logistic regression
glm0_fit = sm.Logit(y01, X).fit(disp=False)
print(glm0_fit.summary())

# Predict probabilities and convert to binary predictions
prob = glm0_fit.predict(X)
pred = (prob > 0.5).astype(int)

# Confusion matrix and accuracy
conf_matrix = pd.crosstab(y01, pred, rownames=['Actual'], colnames=['Predicted'])
print(conf_matrix)

accuracy = (pred == y01).mean()
print(accuracy)