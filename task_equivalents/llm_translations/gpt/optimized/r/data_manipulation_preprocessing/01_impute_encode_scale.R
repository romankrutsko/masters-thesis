library(readr)
library(dplyr)

Auto <- read_csv("data/csv/Auto.csv", na = "?", show_col_types = FALSE) |>
tidyr::drop_na()

Auto <- Auto |>
mutate(mpg01 = if_else(mpg > median(mpg), 1L, 0L)) |>
select(-mpg, -name)

var_no_scale <- c("cylinders", "year", "origin", "mpg01")
var_to_scale <- c("displacement", "horsepower", "weight", "acceleration")

scaled_var <- scale(Auto[, var_to_scale])

df <- bind_cols(
as.data.frame(scaled_var),
Auto |> select(all_of(var_no_scale))
)

x <- df[, seq_len(ncol(df) - 1)]
y <- df$mpg01