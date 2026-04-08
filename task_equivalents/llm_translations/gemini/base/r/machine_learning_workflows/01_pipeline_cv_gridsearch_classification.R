library(e1071)

Auto <- read.csv('data/csv/Auto.csv', na.strings = '?')
Auto <- na.omit(Auto)

Auto$mpg01 <- ifelse(Auto$mpg > median(Auto$mpg), 1, 0)
Auto <- Auto[, !(names(Auto) %in% c('mpg', 'name'))]

var_no_scale <- c('cylinders', 'year', 'origin', 'mpg01')
var_to_scale <- c('displacement', 'horsepower', 'weight', 'acceleration')

scaled_var <- scale(Auto[, var_to_scale])
df <- cbind(as.data.frame(scaled_var), Auto[, var_no_scale])

x <- df[, names(df) != 'mpg01']
y <- as.factor(df$mpg01)

tune(svm, train.x = x, train.y = y, kernel = 'linear', 
     ranges = list(cost = c(0.01, 0.1, 1, 10, 100, 1000)),
     tunecontrol = tune.control(cross = 5))

tune(svm, train.x = x, train.y = y, kernel = 'polynomial', 
     ranges = list(cost = c(0.01, 0.1, 1, 10, 100, 1000), degree = c(2, 3, 4, 5)),
     tunecontrol = tune.control(cross = 5))

tune(svm, train.x = x, train.y = y, kernel = 'radial', 
     ranges = list(cost = c(0.01, 0.1, 1, 10, 100, 1000), gamma = c(0.5, 1, 2, 3)),
     tunecontrol = tune.control(cross = 5))