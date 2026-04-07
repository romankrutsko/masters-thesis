import pandas as pd
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

auto = pd.read_csv("data/csv/Auto.csv", na_values="?", index_col=0).dropna()

auto["mpg01"] = (auto["mpg"] > auto["mpg"].median()).astype(int)
auto = auto.drop(columns=["mpg", "name"])

var_no_scale = ["cylinders", "year", "origin", "mpg01"]
var_to_scale = ["displacement", "horsepower", "weight", "acceleration"]

scaled_var = pd.DataFrame(
    StandardScaler().fit_transform(auto[var_to_scale]),
    columns=var_to_scale,
    index=auto.index,
)
df = pd.concat([scaled_var, auto[var_no_scale]], axis=1)

x = df.iloc[:, :-1]
y = df["mpg01"].astype("category")

ctry = [0.01, 0.1, 1, 10, 100, 1000]
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=1)

tune_out1 = GridSearchCV(
    SVC(kernel="linear"),
    param_grid={"C": ctry},
    cv=cv,
    scoring="accuracy",
    n_jobs=-1,
)
tune_out1.fit(x, y)
print(pd.DataFrame(tune_out1.cv_results_)[["param_C", "mean_test_score", "std_test_score", "rank_test_score"]])

polytry = [2, 3, 4, 5]
tune_out2 = GridSearchCV(
    SVC(kernel="poly"),
    param_grid={"C": ctry, "degree": polytry},
    cv=cv,
    scoring="accuracy",
    n_jobs=-1,
)
tune_out2.fit(x, y)
print(
    pd.DataFrame(tune_out2.cv_results_)[
        ["param_C", "param_degree", "mean_test_score", "std_test_score", "rank_test_score"]
    ]
)

gammatry = [0.5, 1, 2, 3]
tune_out3 = GridSearchCV(
    SVC(kernel="rbf"),
    param_grid={"C": ctry, "gamma": gammatry},
    cv=cv,
    scoring="accuracy",
    n_jobs=-1,
)
tune_out3.fit(x, y)
print(
    pd.DataFrame(tune_out3.cv_results_)[
        ["param_C", "param_gamma", "mean_test_score", "std_test_score", "rank_test_score"]
    ]
)