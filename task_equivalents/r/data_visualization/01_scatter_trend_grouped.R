# Extracted from Ch03.R (Q8 visualization)

auto = read.csv('data/csv/Auto.csv', header=TRUE, na.strings='?')
auto = na.omit(auto)

n = nrow(auto)
X = matrix(auto$horsepower, ncol=1)
Y = matrix(auto$mpg, ncol=1)
X = cbind(1, X)
model1 = lm(Y ~ X[,2])

a = coef(model1)[1]
b = coef(model1)[2]
yfit = a + b * X[,2]

plot(X[,2], Y, xlab='horsepower', ylab='mpg')
lines(X[,2], yfit, col='red')
