library(readr)
library(ggplot2)

# Load data
Auto <- read_csv('data/csv/Auto.csv', na = c("?", "NA")) %>%
  drop_na()

# Fit linear model
model1_fit <- lm(mpg ~ horsepower, data = Auto)

# Predict values
Auto$yfit <- predict(model1_fit, Auto)

# Plot data
ggplot(Auto, aes(x = horsepower, y = mpg)) +
  geom_point() +
  geom_line(aes(y = yfit), color = 'red') +
  labs(x = 'horsepower', y = 'mpg')