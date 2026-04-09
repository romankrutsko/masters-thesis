import pandas as pd
from sklearn.model_selection import train_test_split

# Load the data
College = pd.read_csv('data/csv/College.csv')
College.set_index(College.columns[0], inplace=True)

# Create a new column 'Private01' and drop 'Private'
College['Private01'] = College['Private'].map({'Yes': 1, 'No': 0})
College.drop('Private', axis=1, inplace=True)

# Split data into features (X) and target (Y)
X = College.drop('Apps', axis=1).apply(pd.to_numeric)
Y = College['Apps']

# Split data into training and test sets
xtrain, xtest, ytrain, ytest = train_test_split(X, Y, test_size=0.5, random_state=1)