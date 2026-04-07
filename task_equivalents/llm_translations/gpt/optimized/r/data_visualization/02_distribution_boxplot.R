library(readr)

college <- read_csv("data/csv/College.csv", show_col_types = FALSE)

rownames(college) <- college[[1]]
college <- college[, -1, drop = FALSE]

college$Private <- as.factor(college$Private)
college$Elite <- factor(ifelse(college$Top10perc > 50, "Yes", "No"))

boxplot(Outstate ~ Elite, data = college, xlab = "Elite", ylab = "Outstate")

op <- par(mfrow = c(2, 2))
hist(college$Apps, breaks = 50, xlab = "new applications", main = "")
hist(college$Enroll, breaks = 45, xlab = "new enrollment", main = "")
hist(college$Expend, breaks = 30, xlab = "Instructional expenditure per student", main = "")
hist(college$Outstate, xlab = "Out-of-state tuition", main = "")
par(op)