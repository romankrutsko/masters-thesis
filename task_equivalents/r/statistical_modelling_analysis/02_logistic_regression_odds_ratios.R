# Extracted from Ch04.R (Q10 logistic regression)

Weekly = read.csv('data/csv/Weekly.csv', header=TRUE, row.names=1)

x01 = Weekly[,3:8]
y01 = ifelse(Weekly$Direction == 'Up', 1, 0)

glm0.fit = glm(y01 ~ ., data=x01, family=binomial)
summary(glm0.fit)

prob = predict(glm0.fit, type='response')
pred = ifelse(prob > .5, 1, 0)
table(Actual=y01, Predicted=pred)
mean(pred == y01)

# Previous version
#
# Weekly = read.csv('data/csv/Weekly.csv', header=TRUE, row.names=1)
# Weekly$Direction = as.factor(Weekly$Direction)
#
# glm1.fit = glm(Direction ~ Lag1+Lag2+Lag3+Lag4+Lag5+Volume, data=Weekly, family=binomial)
# summary(glm1.fit)
#
# n         = dim(Weekly)[1]
# glm1.prob = predict(glm1.fit, type='response')
# glm1.pred = rep('Down', n)
# glm1.pred[glm1.prob > .5] = 'Up'
#
# table(glm1.pred, Weekly$Direction)
# mean(glm1.pred == Weekly$Direction)
