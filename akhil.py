from datamodel import OrderDepth, UserId, TradingState, Order
from typing import List
import string

DIFF = 5

def sort_orders_by_target(buy_orders: dict[int, int], sell_orders: dict[int, int], target: float) -> list[tuple[int, int]]:
    """
    Combines buy orders and sell orders (each as dict[price, volume]) and returns
    a list of (price, volume) tuples sorted by an effective distance from the target.

    For buy orders (volume negative): only orders with price above the target are rewarded,
      with effective distance = price - target.
    For sell orders (volume positive): only orders with price below the target are rewarded,
      with effective distance = target - price.

    Orders on the wrong side (buy orders at or below target, sell orders at or above target)
    are considered unprofitable (nonpositive effective distance) and are dropped.

    The returned list is sorted in descending order, meaning that orders with higher (more profitable)
    effective distances come first.
    """
    # Merge the dictionaries into a single list of (price, volume) tuples.
    combined_orders = []
    for price, volume in buy_orders.items():
        combined_orders.append((price, volume))
    for price, volume in sell_orders.items():
        combined_orders.append((price, volume))

    def effective_distance(order: tuple[int, int]) -> float:
        price, volume = order
        # For a buy order (volume negative): we want to sell into it, but only if the price is above target.
        if volume < 0:
            if price > target + DIFF:
                return (price - target)  # Positive: profitable (price above target).
            else:
                return -(target - price)  # Negative: unprofitable (price not above target).
        # For a sell order (volume positive): we want to buy from it, but only if the price is below target.
        elif volume > 0:
            if price < target - DIFF:
                return (target - price)  # Positive: profitable (price below target).
            else:
                return -(price - target)  # Negative: unprofitable.
        # Just in case an order has zero volume.
        return 0

    # Filter out unprofitable orders (i.e. those that have a nonpositive effective distance)
    profitable_orders = [order for order in combined_orders if effective_distance(order) > 0]

    # Sort the profitable orders in descending order (most profitable trades first).
    sorted_orders = sorted(profitable_orders, key=effective_distance, reverse=True)

    return sorted_orders

class Trader:

    POSITION_LIMIT = 50
    position = 0

    pnl = 0

    def run(self, state: TradingState):
        print("traderData: " + state.traderData)
        print("Observations: " + str(state.observations))

        # Orders to be placed on exchange matching engine
        result = {}
        for product in state.order_depths:
            if (product != 'SQUID_INK'):
                continue
            order_depth: OrderDepth = state.order_depths[product]
            orders: List[Order] = []
            print("Buy Order depth : " + str(len(order_depth.buy_orders)) + ", Sell order depth : " + str(
                len(order_depth.sell_orders)))

            best_ask = 0
            best_bid = 0

            if len(order_depth.sell_orders) != 0:
                best_ask = min(list(order_depth.sell_orders.keys()))

            if len(order_depth.buy_orders) != 0:
                best_bid = max(list(order_depth.buy_orders.keys()))


            if best_bid > 0 or best_ask > 0:
                acceptable_price = (best_bid + best_ask) / 2

                print("Acceptable price : " + str(acceptable_price))

                best_orders = sort_orders_by_target(order_depth.buy_orders, order_depth.sell_orders, acceptable_price)

                for (price, volume) in best_orders:
                    if abs(-volume + self.position) <= self.POSITION_LIMIT:
                        if -volume < 0:
                            print(f"BUY {abs(volume)} at {price}")
                        else:
                            print(f"SELL {abs(volume)} at {price}")
                        self.pnl += price * -volume
                        self.position += -volume
                        print(f"PNL: {self.pnl}, Position: {self.position}")
                        orders.append(Order(product, price, -volume))


            result[product] = orders


            # String value holding Trader state data required.
        # It will be delivered as TradingState.traderData on next execution.

        # Sample conversion request. Check more details below.
        conversions = 1
        return result, conversions, state.traderData
