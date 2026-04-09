# Load necessary libraries
library(readr)
library(broom)

# Read data from csv file
Auto <- read_csv('data/csv/Auto.csv', na = c("?", "NA")) %>% 
  drop_na()

# Prepare data for modeling
X <- Auto$horsepower
Y <- Auto$mpg

# Fit linear model
model1_fit <- lm(Y ~ X)

# Print model summary
summary(model1_fit)

# Make prediction for new data point
xnew <- data.frame(X = 98)
pred <- predict(model1_fit, newdata = xnew, interval = "confidence", level = 0.95)
pred_obs <- predict(model1_fit, newdata = xnew, interval = "prediction", level = 0.95)

# Print predictions
print(data.frame(mean = pred[, 1], mean_ci_lower = pred[, 2], mean_ci_upper = pred[, 3]))
print(data.frame(mean = pred[, 1], obs_ci_lower = pred_obs[, 2], obs_ci_upper = pred_obs[, 3]))