library(readr)
library(dplyr)

Auto <- read_csv('data/csv/Auto.csv', na = c("?")) %>%
  drop_na() %>%
  mutate(
    mpg01 = ifelse(mpg > median(mpg), 1, 0)
  ) %>%
  select(-c(mpg, name))

var_no_scale <- c('cylinders', 'year', 'origin', 'mpg01')
var_to_scale <- c('displacement', 'horsepower', 'weight', 'acceleration')

scaled_var <- Auto %>%
  select(all_of(var_to_scale)) %>%
  scale() %>%
  as.data.frame()

df <- bind_cols(scaled_var, Auto %>% select(all_of(var_no_scale)))

x <- df %>% select(-mpg01)
y <- df$mpg01