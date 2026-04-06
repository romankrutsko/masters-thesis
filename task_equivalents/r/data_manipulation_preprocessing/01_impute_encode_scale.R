# Extracted from Ch09.R (Q7 preprocessing/scaling)

library(ISLR)

mpg01 = ifelse(Auto$mpg > median(Auto$mpg), 1, 0)
df    = data.frame(Auto[,2:7], mpg01=mpg01)

# Scale continuous variables; keep binary/categorical-coded columns unscaled.
var_to_scale = c('displacement', 'horsepower', 'weight', 'acceleration')
df[var_to_scale] = scale(df[var_to_scale])

x = df[, colnames(df) != 'mpg01']
y = as.factor(df$mpg01)
