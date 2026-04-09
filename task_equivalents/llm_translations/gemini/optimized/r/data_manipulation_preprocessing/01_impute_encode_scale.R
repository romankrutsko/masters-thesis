Auto <- read.csv('data/csv/Auto.csv', na.strings = '?')
Auto <- na.omit(Auto)

Auto$mpg01 <- as.integer(Auto$mpg > median(Auto$mpg))

var_no_scale <- c('cylinders', 'year', 'origin', 'mpg01')
var_to_scale <- c('displacement', 'horsepower', 'weight', 'acceleration')

df <- data.frame(
  as.data.frame(scale(Auto[, var_to_scale])),
  Auto[, var_no_scale]
)

x <- df[, -ncol(df)]
y <- df$mpg01