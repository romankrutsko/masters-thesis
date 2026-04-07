# Extracted from Ch02.R (Q8 visualization)

college = read.csv('data/csv/College.csv', header=TRUE)
rownames(college) = college[,1]
college = college[,-1]

Elite = rep('No', nrow(college))
Elite[college$Top10perc > 50] = 'Yes'
Elite = as.factor(Elite)
college = data.frame(college, Elite)

plot(college$Elite, college$Outstate, xlab='Elite', ylab='Out-of-state tuition')

dev.new()
par(mfrow=c(2,2))
hist(college$Apps, breaks=50, xlab='new applications', main='')
hist(college$Enroll, breaks=45, xlab='new enrollment', main='')
hist(college$Expend, breaks=30, xlab='Instructional expenditure per student', main='')
hist(college$Outstate, xlab='Out-of-state tuition', main='')
