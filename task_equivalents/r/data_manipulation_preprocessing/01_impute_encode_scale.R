# Extracted from Ch02.R (Q9 preprocessing)

auto = read.csv("C:\\Users\\Carol\\Desktop\\Auto.csv", header=T, na.strings='?')
auto = na.omit(auto)
fix(auto)
summary(auto)
