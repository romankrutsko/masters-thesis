# Install required libraries if needed
# install.packages(c("readr", "dplyr", "ggplot2"))

# Load required libraries
library(readr)
library(dplyr)
library(ggplot2)

# Load data
college <- read_csv("data/csv/College.csv")

# Set row names and drop first column
rownames(college) <- college[, 1]
college <- college[, -1]

# Convert 'Private' to factor
college$Private <- as.factor(college$Private)

# Create 'Elite' column
college$Elite <- ifelse(college$Top10perc > 50, "Yes", "No")
college$Elite <- as.factor(college$Elite)

# Boxplot
ggplot(college, aes(x = Elite, y = Outstate)) +
  geom_boxplot()

# Histograms
ggplot(college) +
  geom_histogram(aes(x = Apps), bins = 50) +
  labs(x = "new applications") +
  theme(aspect.ratio = 1) +
  
  geom_histogram(aes(x = Enroll), bins = 45) +
  labs(x = "new enrollment") +
  theme(aspect.ratio = 1) +
  
  geom_histogram(aes(x = Expend), bins = 30) +
  labs(x = "Instructional expenditure per student") +
  theme(aspect.ratio = 1) +
  
  geom_histogram(aes(x = Outstate)) +
  labs(x = "Out-of-state tuition") +
  theme(aspect.ratio = 1) -> p1

# To display 4 histograms side by side, we can use facet_wrap or grid.arrange from gridExtra package.
# Here we will pivot the data and then plot.
library(tidyr)
college %>%
  select(c(Apps, Enroll, Expend, Outstate)) %>%
  pivot_longer(cols = everything(), names_to = "variable", values_to = "value") %>%
  ggplot(aes(x = value)) +
  geom_histogram(bins = c(rep(50, sum(college$variable == "Apps")), 
                         rep(45, sum(college$variable == "Enroll")), 
                         rep(30, sum(college$variable == "Expend")), 
                         rep(30, sum(college$variable == "Outstate")))[1:nrow(college),]) +
  facet_wrap(~ variable, scales = "free") +
  labs(x = NULL)

# Simple version of the histogram
college %>%
  select(c(Apps, Enroll, Expend, Outstate)) %>%
  pivot_longer(cols = everything(), names_to = "variable", values_to = "value") %>%
  ggplot(aes(x = value)) +
  geom_histogram() +
  facet_wrap(~ variable, scales = "free") +
  labs(x = NULL)