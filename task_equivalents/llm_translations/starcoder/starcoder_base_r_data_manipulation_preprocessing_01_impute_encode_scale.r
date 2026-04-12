Here's the R code that implements this logic:

```r
library(dplyr)
library(caret)
Auto <- read.csv('data/csv/Auto.csv', na.strings='?') %>%
  filter(!is.na(horsepower)) %>% # remove missing values
  mutate(mpg01 = ifelse(mpg > median(mpg), 1, 0),
         cylinders = as.factor(cylinders),
         origin = as.factor(origin))
var_to_scale <- c('displacement', 'horsepower', 'weight', 'acceleration')
preProcValues <- preProcess(Auto[, var_to_scale], method = c("center", "scale"))
scaled_var  <- predict(preProcValues, Auto[, var_to_scale])
df  <- cbind(scaled_var, Auto[, -which(names(Auto) %in% var_to_scale)])
x  <- df[, -(ncol(df)-1)]
y  <- df[, ncol(df)]
```

The `dplyr` library is used to read and preprocess the dataset, while the `caret` library is used for scaling the numeric variables. The `preProcess` function from `caret` is used to scale the numeric variables using the `center` and `scale` methods. The scaled values are then combined with the other variables in the dataframe using the `cbind` function. Finally, the independent and dependent variables are separated into `x` and `y`, respectively.