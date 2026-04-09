library(readr)
library(dplyr)

College <- read_csv('data/csv/College.csv')
College <- College %>% 
  column_to_rownames(var = names(College)[1]) %>% 
  mutate(Private01 = ifelse(Private == 'Yes', 1, 0)) %>% 
  select(-Private, -Apps)

set.seed(1)
train_index <- sample(nrow(College), size = nrow(College) / 2)
xtrain <- College[train_index, setdiff(names(College), 'Apps')] 
ytrain <- College[train_index, 'Apps']
xtest <- College[-train_index, setdiff(names(College), 'Apps')] 
ytest <- College[-train_index, 'Apps']