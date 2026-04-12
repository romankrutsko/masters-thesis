Here is the R code that replicates the behavior and results of the given Python code:


library(tidyverse)
library(data.table)
library(ggplot2)

college = fread('data/csv/College.csv')
school_name = college$V1
college  = college %>%
  rename(School = V1)
college  = college %>%
  remove_rownames() %>%
  column_to_rownames(var = 'School')
college$Private  = as.factor(college$Private)

college  = college %>%
  mutate(Elite = ifelse(Top10perc > 50, "Yes", "No"))
college$Elite  = as.factor(college$Elite)

ggplot(college, aes(x=Elite, y=Outstate)) + geom_boxplot()

par(mfrow = c(2, 2))
hist(college$Apps, xlab="New applications", main="", breaks=50)
hist(college$Enroll, xlab="New enrollment", main="", breaks=45)
hist(college$Expend, xlab="Instructional expenditure per student", main="", breaks=30)
hist(college$Outstate, xlab="Out-of-state tuition", main="")