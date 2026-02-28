# Extracted from Ch09.py (Q7 preprocessing/scaling)

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

Auto = pd.read_csv('C:\\Users\\Carol\\Desktop\\Auto.csv', na_values='?').dropna()

Auto['mpg01'] = np.where(Auto['mpg'] > np.median(Auto['mpg']), 1, 0)
Auto          = Auto.drop(['mpg', 'name'], axis=1)
# scale continuous variables
var_no_scale  = ['cylinders', 'year', 'origin', 'mpg01']
var_to_scale  = ['displacement', 'horsepower', 'weight', 'acceleration']
scaled_var    = StandardScaler().fit_transform(Auto[var_to_scale])
temp1         = pd.DataFrame(scaled_var, columns=var_to_scale)
temp2         = Auto[var_no_scale].reset_index(drop=True)
df            = pd.concat([temp1, temp2], axis=1)
x             = df.iloc[:,:-1]
y             = df['mpg01']
