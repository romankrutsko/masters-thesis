import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import LassoCV
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error

def load_and_clean_data():
    Hitters = pd.read_csv('data/csv/Hitters.csv')
    Hitters.dropna(inplace=True)
    drop_cols = ['rownames', 'Player', 'Name']
    Hitters.drop(columns=drop_cols, inplace=True)
    league_map = {'A': 0, 'N': 1}
    Hitters['League'] = Hitters['League'].replace(league_map)
    newleague_map = {'A': 0, 'N': 1}
    Hitters['NewLeague'] = Hitters['NewLeague'].replace(newleague_map)
    division_map = {'E': 0, 'W': 1}
    Hitters['Division'] = Hitters['Division'].replace(division_map)
    Hitters['logSal'] = np.log(Hitters['Salary'])

    return Hitters


def split_data(data):
    x = data.drop(['Salary', 'logSal'], axis=1)
    y = data['logSal']
    xtrain, xtest, ytrain, ytest = train_test_split(x, y, test_size=0.2, random_state=42)

    return xtrain, xtest, ytrain, ytest


def fit_boosting_model(xtrain, ytrain):
    boost_model = GradientBoostingRegressor()
    boost_model.fit(xtrain, ytrain)

    return boost_model


def fit_lasso_model(xtrain, ytrain):
    lasso_model = LassoCV(cv=5)
    lasso_model.fit(xtrain, ytrain)

    return lasso_model


def evaluate_models(boost_model, lasso_model, xtest, ytest):
    boost_pred = boost_model.predict(xtest)
    lasso_pred = lasso_model.predict(xtest)
    boost_mse = mean_squared_error(ytest, boost_pred)
    lasso_mse = mean_squared_error(ytest, lasso_pred)

    return boost_mse, lasso_mse


def main():
    data = load_and_clean_data()
    xtrain, xtest, ytrain, ytest = split_data(data)
    boost_model = fit_boosting_model(xtrain, ytrain)
    lasso_model = fit_lasso_model(xtrain, ytrain)
    boost_mse, lasso_mse = evaluate_models(boost_model, lasso_model, xtest, ytest)
    print("Gradient Boosting MSE:", boost_mse)
    print("Lasso Regression MSE:", lasso_mse)

if __name__ == "__main__":
    main()
