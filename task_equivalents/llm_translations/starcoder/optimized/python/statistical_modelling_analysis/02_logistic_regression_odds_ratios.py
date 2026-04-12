import pandas as pd
Weekly = pd.read_csv('data/csv/Weekly.csv', index_col=0)
x01 = Weekly.iloc[:,2:8] # Select columns 3 to 8
y01 = (Weekly['Direction'] == 'Up').astype(int) # Convert to binary values 0 and 1
from sklearn.linear_model import LogisticRegression
glm0_fit = LogisticRegression().fit(x01, y01)
print(glm0_fit.intercept_, glm0_fit.coef_)
prob = glm0_fit.predict_proba(x01)[:, 1] # Probability of class 1 (Up)
pred = (prob > 0.5).astype(int) # Predicted values as binary 0 and 1
from sklearn.metrics import confusion_matrix, accuracy_score
print(confusion_matrix(y01, pred))
print(accuracy_score(y01, pred))
