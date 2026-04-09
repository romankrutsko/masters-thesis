# Install and load necessary libraries
# install.packages(c("readr", "dplyr", "caret", "kernlab"))
library(readr)
library(dplyr)
library(caret)
library(kernlab)

# Load data
Auto <- read_csv('data/csv/Auto.csv', na = c("?")) %>%
  drop_na()

# Create binary variable mpg01
Auto$mpg01 <- ifelse(Auto$mpg > median(Auto$mpg, na.rm = TRUE), 1, 0)
Auto <- Auto %>%
  select(-c(mpg, name))

# Define variables to scale and not to scale
var_no_scale <- c('cylinders', 'year', 'origin', 'mpg01')
var_to_scale <- c('displacement', 'horsepower', 'weight', 'acceleration')

# Scale variables
scaled_var <- scale(Auto[, var_to_scale])
df <- data.frame(scaled_var, Auto[, var_no_scale])

# Split data into features and target
x <- df[, !names(df) %in% "mpg01"]
y <- df$mpg01

# Define train control
train_control <- trainControl(method = "cv", number = 5, 
                               savePredictions = "final", 
                               classProbs = TRUE)

# Linear kernel
tune_grid_linear <- expand.grid(C = c(0.01, 0.1, 1, 10, 100, 1000))
set.seed(123) # For reproducibility
linear_svm <- train(x, y, 
                    method = "svmLinear", 
                    tuneGrid = tune_grid_linear, 
                    trControl = train_control)

# Polynomial kernel
tune_grid_poly <- expand.grid(C = c(0.01, 0.1, 1, 10, 100, 1000), 
                              degree = c(2, 3, 4, 5), 
                              scale = c(1))
set.seed(123) # For reproducibility
poly_svm <- train(x, y, 
                  method = "svmPoly", 
                  tuneGrid = tune_grid_poly, 
                  trControl = train_control)

# Radial kernel
tune_grid_rbf <- expand.grid(sigma = c(0.5, 1, 2, 3), 
                             C = c(0.01, 0.1, 1, 10, 100, 1000))
# Map C and sigma to the required format for kernlab's ksvm
tune_grid_rbf <- expand.grid(C = c(0.01, 0.1, 1, 10, 100, 1000), 
                             sigma = c(0.5, 1, 2, 3))
set.seed(123) # For reproducibility
rbf_svm <- train(x, y, 
                 method = "svmRadial", 
                 tuneGrid = tune_grid_rbf, 
                 trControl = train_control)