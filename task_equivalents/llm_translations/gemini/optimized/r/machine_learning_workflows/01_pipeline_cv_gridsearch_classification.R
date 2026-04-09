library(e1071)

Auto <- read.csv('data/csv/Auto.csv', na.strings = '?')
Auto <- na.omit(Auto)

Auto$mpg01 <- as.factor(as.integer(Auto$mpg > median(Auto$mpg)))

var_no_scale <- c('cylinders', 'year', 'origin', 'mpg01')
var_to_scale <- c('displacement', 'horsepower', 'weight', 'acceleration')

df <- data.frame(
  scale(Auto[, var_to_scale]),
  Auto[, var_no_scale]
)

tune_ctrl <- tune.control(cross = 5)

tune(svm, mpg01 ~ ., data = df, kernel = "linear",
     ranges = list(cost = c(0.01, 0.1, 1, 10, 100, 1000)),
     tunecontrol = tune_ctrl)

tune(svm, mpg01 ~ ., data = df, kernel = "polynomial",
     ranges = list(cost = c(0.01, 0.1, 1, 10, 100, 1000), degree = c(2, 3, 4, 5)),
     tunecontrol = tune_ctrl)

tune(svm, mpg01 ~ ., data = df, kernel = "radial",
     ranges = list(cost = c(0.01, 0.1, 1, 10, 100, 1000), gamma = c(0.5, 1, 2, 3)),
     tunecontrol = tune_ctrl)