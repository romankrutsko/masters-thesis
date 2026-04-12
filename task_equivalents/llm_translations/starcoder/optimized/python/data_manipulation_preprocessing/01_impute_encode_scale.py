import pandas as pd
from sklearn import preprocessing

def translate_code():
    df = pd.read_csv('data/csv/Auto.csv', na_values='?', index_col=1)
    df = df.dropna()

    df['mpg01'] = (df['mpg'] > df['mpg'].median()).astype(int)
    df = df.drop(['mpg', 'name'], axis=1)
    
    var_no_scale = ['cylinders', 'year', 'origin', 'mpg01']
    var_to_scale = ['displacement', 'horsepower', 'weight', 'acceleration']
    scaled_var = preprocessing.scale(df[var_to_scale])
    df = pd.concat([pd.DataFrame(scaled_var, columns=var_to_scale),
                    df[var_no_scale]], axis=1)
    
    x = df.drop('mpg01', axis=1)
    y = df['mpg01']

    return x, y
x, y = translate_code()
