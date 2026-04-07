library(readr)
library(dplyr)

college <- read_csv("data/csv/College.csv")

school_name <- college[[1]]
rownames(college) <- school_name
college <- college[, -1]

college$Private <- as.factor(college$Private)

college$Elite <- ifelse(college$Top10perc > 50, "Yes", "No")
college$Elite <- as.factor(college$Elite)

boxplot(Outstate ~ Elite, data = college,
xlab = "Elite", ylab = "Outstate")

par(mfrow = c(2, 2))
hist(college$Apps, breaks = 50, xlab = "new applications", main = "")
hist(college$Enroll, breaks = 45, xlab = "new enrollment", main = "")
hist(college$Expend, breaks = 30, xlab = "Instructional expenditure per student", main = "")
hist(college$Outstate, xlab = "Out-of-state tuition", main = "")