# Extracted from Ch09.R (Q7 SVM tuning workflow)

library(e1071)
Auto = read.csv('data/csv/Auto.csv', header=TRUE, na.strings='?', row.names=1)
Auto = na.omit(Auto)

Auto$mpg01 = ifelse(Auto$mpg > median(Auto$mpg), 1, 0)
Auto = subset(Auto, select=-c(mpg, name))

var_no_scale = c('cylinders', 'year', 'origin', 'mpg01')
var_to_scale = c('displacement', 'horsepower', 'weight', 'acceleration')
scaled_var = scale(Auto[, var_to_scale])
df = cbind(as.data.frame(scaled_var), Auto[, var_no_scale])

x = df[, -ncol(df)]
y = as.factor(df$mpg01)
ctry = c(0.01, 0.1, 1, 10, 100, 1000)
tune_ctrl = tune.control(cross=5)

set.seed(1)
tune.out1 = tune(svm, x=x, y=y, kernel='linear', ranges=list(cost=ctry), tunecontrol=tune_ctrl)
summary(tune.out1)

polytry = c(2, 3, 4, 5)
set.seed(1)
tune.out2 = tune(svm, x=x, y=y, kernel='polynomial', ranges=list(cost=ctry, degree=polytry), tunecontrol=tune_ctrl)
summary(tune.out2)

gammatry = c(0.5, 1, 2, 3)
set.seed(1)
tune.out3 = tune(svm, x=x, y=y, kernel='radial', ranges=list(cost=ctry, gamma=gammatry), tunecontrol=tune_ctrl)
summary(tune.out3)
