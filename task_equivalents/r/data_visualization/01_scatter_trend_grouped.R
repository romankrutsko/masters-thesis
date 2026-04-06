# Extracted from Ch03.R (Q8 visualization)

auto = read.csv('data/csv/Auto.csv', header=TRUE, na.strings='?')
auto = na.omit(auto)
model1 = lm(mpg~horsepower, data=auto)

plot(auto$horsepower, auto$mpg)
abline(model1, lwd=3, col='red')
