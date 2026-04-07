library(readr)
library(dplyr)

Auto <- read_csv("data/csv/Auto.csv", na = "?") %>%
na.omit()

Auto <- Auto %>%
mutate(mpg01 = ifelse(mpg > median(mpg), 1, 0)) %>%
select(-mpg, -name)

var_no_scale <- c("cylinders", "year", "origin", "mpg01")
var_to_scale <- c("displacement", "horsepower", "weight", "acceleration")

scaled_var <- scale(Auto[, var_to_scale])

df <- bind_cols(
as.data.frame(scaled_var) %>% setNames(var_to_scale),
Auto[, var_no_scale]
)

x <- df[, 1:(ncol(df) - 1)]
y <- df$mpg01