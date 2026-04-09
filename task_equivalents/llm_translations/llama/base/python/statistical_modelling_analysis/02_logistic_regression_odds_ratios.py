import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix

# Load data
weekly = pd.read_csv('data/csv/Weekly.csv', index_col=0)

# Prepare data
x01 = weekly.iloc[:, 2:8]
y01 = (weekly['Direction'] == 'Up').astype(int)

# Fit logistic regression model
glm0_fit = LogisticRegression(max_iter=1000)
glm0_fit.fit(x01, y01)

# Print model summary (coefficients)
print('Coefficients:', glm0_fit.coef_)
print('Intercept:', glm0_fit.intercept_)

# Predict probabilities and classes
prob = glm0_fit.predict_proba(x01)[:, 1]
pred = (prob > 0.5).astype(int)

# Evaluate model
print(confusion_matrix(y01, pred))
print('Accuracy:', accuracy_score(y01, pred))