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
