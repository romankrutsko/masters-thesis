# Extracted from Ch02.R (Q8 visualization)

college = read.csv("C:\\Users\\Carol\\Desktop\\College.csv", header=T)
rownames(college) = college[,1]
college = college[,-1]

Elite = rep("No", nrow(college))
Elite[college$Top10perc > 50] = "Yes"
Elite = as.factor(Elite)
college = data.frame(college, Elite)

plot(college$Elite, college$Outstate, xlab='Elite',ylab='Out-of-state tuition')

dev.new()
par(mfrow=c(2,2))
hist(college$Apps, breaks=50, main='# of applications')
hist(college$Enroll, breaks=25, main='# of new enrollment')
hist(college$Expend, breaks =10, main='Instructional expenditure per student')
hist(college$Outstate, main='Out-of-state tuition')
