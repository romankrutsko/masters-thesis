# Extracted from Ch06.R (Q9 preprocessing/model matrix)

College = read.csv("C:\\Users\\Carol\\Desktop\\College.csv", header=T)
rownames(College) = College[,1]
College = College[,-1]

set.seed(1)
train    = sample(1:nrow(College), nrow(College)/2)
test     = (-train)
df.train = College[train,]
df.test  = College[test,]

x.train = model.matrix(Apps~., df.train)[,-1]
y.train = df.train$Apps
x.test  = model.matrix(Apps~., df.test)[,-1]
y.test  = df.test$Apps
