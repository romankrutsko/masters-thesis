library(tidyverse)

college <- read_csv("data/csv/College.csv") %>%
  rename(School = X1) %>%
  mutate(Private = as_factor(Private),
         Elite = ifelse(Top10perc > 50, "Yes", "No"))

ggplot(college, aes(x = Elite, y = Outstate)) +
  geom_boxplot()

grid.arrange(
  ggplot(college, aes(Apps)) + geom_histogram(bins = 50) + xlab("New applications"),
  ggplot(college, aes(Enroll)) + geom_histogram(bins = 45) + xlab("New enrollment"),
  ggplot(college, aes(Expend)) + geom_histogram(bins = 30) + xlab("Instructional expenditure per student"),
  ggplot(college, aes(Outstate)) + geom_histogram() + xlab("Out-of-state tuition"),
  nrow = 2,
  ncol = 2
)
