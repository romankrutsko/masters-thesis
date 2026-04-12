The following code snippet provides the Python equivalent of the given R code:

```python
import pandas as pd

College = pd.read_csv('data/csv/College.csv', header=0)
College.set_index(College.columns[0], inplace=True)
College['Private01'] = (College['Private'] == 'Yes').astype(int)
College.drop(columns='Private', inplace=True)
X = College.drop(columns='Apps').apply(pd.to_numeric)
Y = College['Apps']

from sklearn.model_selection import train_test_split
X_train, X_test, y_train, y_test = train_test_split(X, Y, test_size=0.5, random_state=1)
```

In the Python code:
- `import pandas as pd` imports the Pandas library and assigns it to the alias `pd`.
- `College = pd.read_csv('data/csv/College.csv', header=0)` reads the CSV file 'College.csv' from the specified path, assuming the first row contains column headers.
- `College.set_index(College.columns[0], inplace=True)` sets the first column as the index of the DataFrame `College`.
- `College['Private01'] = (College['Private'] == 'Yes').astype(int)` creates a new column `Private01` in the `College` DataFrame, where the value is 1 if the corresponding value in the `Private` column is 'Yes', and 0 otherwise.
- `College.drop(columns='Private', inplace=True)` drops the `Private` column from the `College` DataFrame.
- `X = College.drop(columns='Apps').apply(pd.to_numeric)` creates a new DataFrame `X` by dropping the `Apps` column from the `College` DataFrame and converting all columns to numeric data types.
- `Y = College['Apps']` creates a new Series `Y` containing only the values in the `Apps` column of the `College` DataFrame.
- `from sklearn.model_selection import train_test_split` imports the `train_test_split` function from the `sklearn.model_selection` module.
- `X_train, X_test, y_train, y_test = train_test_split(X, Y, test_size=0.5, random_state=1)` splits the data into training and testing sets with a 50/50 split, setting the `random_state` to 1 for reproducibility.

The resulting variables `X_train`, `X_test`, `y_train`, and `y_test` can be used as inputs for machine learning models or other analyses.