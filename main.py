import batscrape
import grapher


car = input("Enter the car model you want to search for: ")
mileage = input("Enter the mileage of the car: ")

#run scraper to get auction data for the car model
previous_auctions = batscrape.scrape_auctions(car)

#clean data and remove outliers
points = grapher.clean_auction_data(previous_auctions)

#find weights for best fit polynomial regression model
best_degree, best_weights, best_error = grapher.fit_best_model(points)

#calculate expected price based on mileage and best fit model weights
expected_price = grapher.expected_price(int(mileage), best_weights)
price_low = expected_price * 0.9
price_high = expected_price * 1.1
print(f"Expected price for {car} with {mileage} miles would be between ${price_low:.2f} - ${price_high:.2f}")

grapher.graph_auctions(points, best_weights)

