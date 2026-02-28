# Extracted from Ch03.R (Q8 linear regression + inference)

auto = read.csv("C:\\Users\\Carol\\Desktop\\Auto.csv", header=T, na.strings='?')
auto = na.omit(auto)
fix(auto)

model1 = lm(mpg~horsepower, data=auto)
summary(model1)

predict(model1, data.frame(horsepower=98), interval="confidence")
predict(model1, data.frame(horsepower=98), interval="prediction")
