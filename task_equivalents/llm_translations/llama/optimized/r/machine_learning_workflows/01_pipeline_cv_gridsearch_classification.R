# Install required packages if not already installed
# install.packages(c("readr", "dplyr", "caret", "kernlab"))

# Load necessary libraries
library(readr)
library(dplyr)
library(caret)
library(kernlab)

# Load data
Auto <- read_csv('data/csv/Auto.csv', na = c("?", "NA")) %>%
  drop_na()

# Create binary mpg variable
Auto$mpg01 <- ifelse(Auto$mpg > median(Auto$mpg), 1, 0)
Auto <- Auto %>% 
  select(-c(mpg, name))

# Scale variables
var_no_scale <- c('cylinders', 'year', 'origin', 'mpg01')
var_to_scale <- c('displacement', 'horsepower', 'weight', 'acceleration')
preProc <- preProcess(Auto[, var_to_scale], method = c("center", "scale"))
df <- data.frame(predict(preProc, Auto[, var_to_scale]), 
                 Auto[, var_no_scale])

# Split data into features (x) and target (y)
x <- df %>% select(-mpg01)
y <- df$mpg01

# Define training control
train_control <- trainControl(method = "cv", 
                               number = 5, 
                               savePredictions = "final", 
                               classProbs = TRUE)

# Tune linear SVM model
tune_grid_linear <- expand.grid(C = c(0.01, 0.1, 1, 10, 100, 1000))
svm_linear <- train(x, y, 
                     method = "svmLinear", 
                     tuneGrid = tune_grid_linear, 
                     trControl = train_control)

# Tune polynomial SVM model
tune_grid_poly <- expand.grid(C = c(0.01, 0.1, 1, 10, 100, 1000), 
                              degree = c(2, 3, 4, 5), 
                              scale = 1)
svm_poly <- train(x, y, 
                  method = "svmPoly", 
                  tuneGrid = tune_grid_poly, 
                  trControl = train_control)

# Tune radial SVM model
tune_grid_rbf <- expand.grid(sigma = c(0.5, 1, 2, 3), 
                             C = c(0.01, 0.1, 1, 10, 100, 1000))
svm_rbf <- train(x, y, 
                 method = "svmRadial", 
                 tuneGrid = tune_grid_rbf, 
                 trControl = train_control)