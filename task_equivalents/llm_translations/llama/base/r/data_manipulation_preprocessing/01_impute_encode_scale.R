library(readr)
library(dplyr)

Auto <- read_csv('data/csv/Auto.csv', na = "?", 
                 col_types = cols(name = col_character())) %>%
  drop_na()

Auto$mpg01 <- ifelse(Auto$mpg > median(Auto$mpg, na.rm = TRUE), 1, 0)
Auto <- Auto %>% select(-mpg, -name)

var_no_scale <- c('cylinders', 'year', 'origin', 'mpg01')
var_to_scale <- c('displacement', 'horsepower', 'weight', 'acceleration')

scaled_var <- scale(Auto[, var_to_scale])
df <- cbind.data.frame(scaled_var, Auto[, var_no_scale])

x <- df %>% select(-mpg01)
y <- df$mpg01