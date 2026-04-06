# Extracted from Ch09.R (Q7 SVM tuning workflow)

library(ISLR)
library(e1071)

mpg01 = ifelse(Auto$mpg > median(Auto$mpg), 1, 0)
df    = data.frame(x=Auto[,2:7], y=as.factor(mpg01))

ctry = c(0.01, 0.1, 1, 10, 100, 1000)

set.seed(1)
tune.out1 = tune(svm, y~., data=df, kernel='linear', ranges=list(cost=ctry))
summary(tune.out1)

polytry = c(2, 3, 4, 5)
set.seed(1)
tune.out2 = tune(svm, y~., data=df, kernel='polynomial', ranges=list(cost=ctry, degree=polytry))
summary(tune.out2)

gammatry = c(0.5, 1, 2, 3)
set.seed(1)
tune.out3 = tune(svm, y~., data=df, kernel='radial', ranges=list(cost=ctry, gamma=gammatry))
summary(tune.out3)
