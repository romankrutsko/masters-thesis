# Load necessary libraries
library(readr)
library(dplyr)
library(ggplot2)

# Read the CSV file
college <- read_csv('data/csv/College.csv')

# Rename the first column to 'School' and set it as the row names
college <- college %>% 
  rename(School = 1) %>% 
  tibble::column_to_rownames('School')

# Convert 'Private' to a factor
college$Private <- as.factor(college$Private)

# Create a new column 'Elite'
college$Elite <- ifelse(college$Top10perc > 50, 'Yes', 'No')
college$Elite <- as.factor(college$Elite)

# Boxplot
ggplot(college, aes(x = Elite, y = Outstate)) + 
  geom_boxplot()

# Histograms
library(gridExtra)
p1 <- ggplot(college, aes(x = Apps)) + 
  geom_histogram(bins = 50) + 
  labs(x = 'new applications')
p2 <- ggplot(college, aes(x = Enroll)) + 
  geom_histogram(bins = 45) + 
  labs(x = 'new enrollment')
p3 <- ggplot(college, aes(x = Expend)) + 
  geom_histogram(bins = 30) + 
  labs(x = 'Instructional expenditure per student')
p4 <- ggplot(college, aes(x = Outstate)) + 
  geom_histogram() + 
  labs(x = 'Out-of-state tuition')

grid.arrange(p1, p2, p3, p4, ncol = 2, nrow = 2)