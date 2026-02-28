# Extracted from Ch08.py (Q8 preprocessing)

import pandas as pd

Carseats = pd.read_csv('C:\\Users\\Carol\\Desktop\\Carseats.csv')
Carseats.head()

Carseats['Urban']     = Carseats.Urban.map({'No':0, 'Yes':1})
Carseats['US']        = Carseats.US.map({'No':0, 'Yes':1})
Carseats['ShelveLoc'] = pd.factorize(Carseats.ShelveLoc)[0]
Carseats              = Carseats.drop('Unnamed: 0', axis=1)
