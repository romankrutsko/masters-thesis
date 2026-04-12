import pandas as pd
from sklearn import preprocessing
from sklearn import svm
from sklearn.model_selection import train_test_split
from sklearn.model_selection import GridSearchCV


def translate_r2python():
    auto = pd.read_csv('data/csv/Auto.csv', na_values='?', index_col=0)
    auto.dropna(inplace=True)

    auto['mpg01'] = (auto['mpg'] > auto['mpg'].median()).astype(int)
    auto = auto.loc[:, ['cylinders', 'displacement', 'horsepower', 'weight', 'acceleration',
                        'year', 'origin', 'mpg01']]

    var_no_scale = ['cylinders', 'year', 'origin', 'mpg01']
    var_to_scale = ['displacement', 'horsepower', 'weight', 'acceleration']
    scaled_var = preprocessing.scale(auto[var_to_scale])
    df = pd.DataFrame(scaled_var, columns=var_to_scale)
    df['mpg01'] = auto['mpg01']

    X = df.iloc[:, :-1]
    y = df.iloc[:, -1]

    c_range = [0.01, 0.1, 1, 10, 100, 1000]
    param_grid = {'C': c_range}
    linear_svc = svm.SVC(kernel='linear')
    grid_search = GridSearchCV(estimator=linear_svc, param_grid=param_grid)
    grid_search.fit(X, y)
    print("Best parameters for linear kernel: ", grid_search.best_params_)
    print("Best score for linear kernel: ", grid_search.best_score_)

    poly_degree = [2, 3, 4, 5]
    param_grid = {'C': c_range, 'degree': poly_degree}
    poly_svc = svm.SVC(kernel='poly')
    grid_search = GridSearchCV(estimator=poly_svc, param_grid=param_grid)
    grid_search.fit(X, y)
    print("Best parameters for polynomial kernel: ", grid_search.best_params_)
    print("Best score for polynomial kernel: ", grid_search.best_score_)

    gamma = [0.5, 1, 2, 3]
    param_grid = {'C': c_range, 'gamma': gamma}
    rbf_svc = svm.SVC(kernel='rbf')
    grid_search = GridSearchCV(estimator=rbf_svc, param_grid=param_grid)
    grid_search.fit(X, y)
    print("Best parameters for RBF kernel: ", grid_search.best_params_)
    print("Best score for RBF kernel: ", grid_search.best_score_)


if __name__ == "__main__":
    translate_r2python()
