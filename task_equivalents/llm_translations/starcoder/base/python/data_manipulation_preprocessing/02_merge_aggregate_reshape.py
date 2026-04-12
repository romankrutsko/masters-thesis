import pandas as pd

College = pd.read_csv('data/csv/College.csv', header=0)
College.set_index(College.columns[0], inplace=True)
College['Private01'] = (College['Private'] == 'Yes').astype(int)
College.drop(columns='Private', inplace=True)
X = College.drop(columns='Apps').apply(pd.to_numeric)
Y = College['Apps']

from sklearn.model_selection import train_test_split
X_train, X_test, y_train, y_test = train_test_split(X, Y, test_size=0.5, random_state=1)