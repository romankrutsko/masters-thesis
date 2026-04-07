import pandas as pd
from sklearn.model_selection import GridSearchCV
from sklearn.svm import SVC

Auto = pd.read_csv("data/csv/Auto.csv", header=0, na_values="?", index_col=0)

mpg01 = (Auto["mpg"] > Auto["mpg"].median()).astype(int)
df = Auto.iloc[:, 1:7].copy()
df["y"] = pd.Categorical(mpg01)

ctry = [0.01, 0.1, 1, 10, 100, 1000]

X = df.drop(columns="y")
y = df["y"]

tune_out1 = GridSearchCV(
    SVC(kernel="linear"),
    param_grid={"C": ctry},
    cv=10,
    n_jobs=-1
)
tune_out1.fit(X, y)
print("Linear kernel best params:", tune_out1.best_params_)
print("Linear kernel best score:", tune_out1.best_score_)
print(pd.DataFrame(tune_out1.cv_results_)[["param_C", "mean_test_score", "std_test_score", "rank_test_score"]])

polytry = [2, 3, 4, 5]

tune_out2 = GridSearchCV(
    SVC(kernel="poly"),
    param_grid={"C": ctry, "degree": polytry},
    cv=10,
    n_jobs=-1
)
tune_out2.fit(X, y)
print("Polynomial kernel best params:", tune_out2.best_params_)
print("Polynomial kernel best score:", tune_out2.best_score_)
print(pd.DataFrame(tune_out2.cv_results_)[["param_C", "param_degree", "mean_test_score", "std_test_score", "rank_test_score"]])

gammatry = [0.5, 1, 2, 3]

tune_out3 = GridSearchCV(
    SVC(kernel="rbf"),
    param_grid={"C": ctry, "gamma": gammatry},
    cv=10,
    n_jobs=-1
)
tune_out3.fit(X, y)
print("Radial kernel best params:", tune_out3.best_params_)
print("Radial kernel best score:", tune_out3.best_score_)
print(pd.DataFrame(tune_out3.cv_results_)[["param_C", "param_gamma", "mean_test_score", "std_test_score", "rank_test_score"]])