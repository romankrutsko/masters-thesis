Auto <- read.csv('data/csv/Auto.csv', na.strings = '?')
Auto <- na.omit(Auto)

Auto$mpg01 <- ifelse(Auto$mpg > median(Auto$mpg), 1, 0)
Auto <- Auto[, !(names(Auto) %in% c('mpg', 'name'))]

var_no_scale <- c('cylinders', 'year', 'origin', 'mpg01')
var_to_scale <- c('displacement', 'horsepower', 'weight', 'acceleration')

scaled_var <- scale(Auto[, var_to_scale])
df <- cbind(as.data.frame(scaled_var), Auto[, var_no_scale])

x <- df[, -ncol(df)]
y <- df$mpg01