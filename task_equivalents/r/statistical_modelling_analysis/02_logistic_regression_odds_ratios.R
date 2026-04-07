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
