import batscrape
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import mean_squared_error
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import make_pipeline


def clean_auction_data(previous_auctions: list[dict]) -> np.ndarray:
    #extract miles and price for scatter plot, filtering out entries with invalid data
    filtered = [
        auction for auction in previous_auctions
        if auction["miles"] is not None and auction["price"] is not None
    ]

    x = [auction["miles"] for auction in filtered]
    y = [auction["price"] for auction in filtered]

    points = np.array(list(zip(x, y)))

    # points should be a 2‑column array; if the caller accidentally passed a
    # list-of-dicts directly to graph_auctions we’ll catch that later.

    miles = points[:, 0]
    prices = points[:, 1]

    #clean data and remove outliers using interquartile range method
    def remove_outliers_iqr(data):
        q1 = np.percentile(data, 25)
        q3 = np.percentile(data, 75)
        iqr = q3 - q1

        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr

        return (data >= lower) & (data <= upper)

    mask = remove_outliers_iqr(miles) & remove_outliers_iqr(prices)

    clean_points = points[mask]
    return clean_points

def graph_auctions(points, best_weights):
    # ensure we have a NumPy array with shape (n,2)
    pts = np.asarray(points)
    if pts.ndim != 2 or pts.shape[1] != 2:
        raise ValueError("graph_auctions expects an array of shape (n,2)", pts.shape)


    if best_weights is not None:
        x = np.linspace(min(pts[:, 0]), max(pts[:, 0]), 100)
        y = [expected_price(xi, best_weights) for xi in x]
        plt.plot(x, y, color='red', label='Best Fit Curve')
        plt.legend()
    #create scatter plot
    plt.scatter(pts[:, 0], pts[:, 1])

    # Add title and labels (optional)
    plt.title("Mileage vs. Price")
    plt.xlabel("Car Mileage (Miles)")
    plt.ylabel("Car Price (USD)")

    plt.show()


#tries multiple polynomial regression models and returns the best fit based on mean squared error
def fit_best_model(points, max_degree=5):

    points = np.array(points)
    X = points[:, 0].reshape(-1, 1)
    y = points[:, 1]

    best_error = float("inf")
    best_degree = None
    best_weights = None

    for degree in range(1, max_degree + 1):

        # Build design matrix manually so we get weights. we want an (n,degree+1)
        # array where column d is X**d. previously we used vstack then transpose,
        # which produced [(degree+1)*n,1] followed by a transpose and led to
        # incompatible dimensions once y had length n. use hstack/column_stack
        # instead.
        A = np.hstack([X**d for d in range(degree + 1)])

        # sanity check: A should have one row per sample
        if A.shape[0] != y.shape[0]:
            raise ValueError(f"design matrix has wrong number of rows {A.shape} vs y {y.shape}")

        # Solve least squares
        weights, _, _, _ = np.linalg.lstsq(A, y, rcond=None)

        predictions = A @ weights
        error = mean_squared_error(y, predictions)

        if error < best_error:
            best_error = error
            best_degree = degree
            best_weights = weights

    return best_degree, best_weights, best_error


#function to calculate expected price based on mileage using the best fit model
def expected_price(mileage: float, weights: list[float]) -> float:
    return sum(weights[i] * (mileage ** i) for i in range(len(weights)))

