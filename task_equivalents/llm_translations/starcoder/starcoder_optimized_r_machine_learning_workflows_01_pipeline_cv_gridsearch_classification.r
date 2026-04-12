```{python}
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import GridSearchCV
from sklearn.svm import SVC
```

```{r}
library(tidyverse)
library(e1071)
```


```{python}
Auto  = pd.read_csv('data/csv/Auto.csv', na_values='?').dropna()
Auto['mpg01']  = np.where(Auto['mpg']  > np.median(Auto['mpg']), 1, 0)
Auto  = Auto.drop(['mpg', 'name'], axis=1)

var_no_scale  = ['cylinders', 'year', 'origin', 'mpg01']
var_to_scale  = ['displacement', 'horsepower', 'weight', 'acceleration']
scaled_var  = StandardScaler().fit_transform(Auto[var_to_scale])
df  = pd.concat([
    pd.DataFrame(scaled_var, columns=var_to_scale),
    Auto[var_no_scale].reset_index(drop=True)
], axis=1)

x  = df.iloc[:, :-1]
y  = df['mpg01']
```

```{r}
Auto <- read_csv("data/csv/Auto.csv", na="?") %>% drop_na()
Auto <- Auto %>%
  mutate(
    mpg01 = ifelse(mpg > median(mpg), 1, 0)
  ) %>%
  select(-mpg, -name)
var_no_scale <- c("cylinders", "year", "origin", "mpg01")
var_to_scale <- c("displacement", "horsepower", "weight", "acceleration")
scaled_var <- scale(Auto[, var_to_scale])
df <- data.frame(
  scaled_var,
  Auto[, var_no_scale]
)
x  = df[, -ncol(df)]
y  = df$mpg01
```


```{python}
tune_param  = [{'C': [0.01, 0.1, 1, 10, 100, 1000]}]
GridSearchCV(SVC(kernel='linear'), tune_param, cv=5, scoring='accuracy', n_jobs=-1).fit(x, y)
```

```{r}
tune_param <- list(C = c(0.01, 0.1, 1, 10, 100, 1000))
svm_linear <- tune(
  svm,
  train.x = x,
  train.y = y,
  kernel = "linear",
  ranges = tune_param,
  tunecontrol = tune.control(cross = 5)
)
```


```{python}
tune_param  = [{'C': [0.01, 0.1, 1, 10, 100, 1000], 'degree': [2, 3, 4, 5]}]
GridSearchCV(SVC(kernel='poly'), tune_param, cv=5, scoring='accuracy', n_jobs=-1).fit(x, y)
```

```{r}
tune_param <- list(C = c(0.01, 0.1, 1, 10, 100, 1000), degree = 2:5)
svm_poly <- tune(
  svm,
  train.x = x,
  train.y = y,
  kernel = "polynomial",
  ranges = tune_param,
  tunecontrol = tune.control(cross = 5)
)
```


```{python}
tune_param  = [{'C': [0.01, 0.1, 1, 10, 100, 1000], 'gamma': [0.5, 1, 2, 3]}]
GridSearchCV(SVC(kernel='rbf'), tune_param, cv=5, scoring='accuracy', n_jobs=-1).fit(x, y)
```

```{r}
tune_param <- list(C = c(0.01, 0.1, 1, 10, 100, 1000), gamma = c(0.5, 1, 2, 3))
svm_radial <- tune(
  svm,
  train.x = x,
  train.y = y,
  kernel = "radial",
  ranges = tune_param,
  tunecontrol = tune.control(cross = 5)
)
```