import random


def run_simulation(k=0.25, steps=20):
    fair_value = 100
    half_spread = 1

    customer_sensitivity = 0.2
    spread_sensitivity = 0.25

    price_move_size = 1
    inventory_limit = 5

    cash = 0
    inventory = 0

    max_abs_inventory = 0

    for trade in range(1, steps + 1):

        # 1. Fair value moves
        if trade > 1:
            price_move = random.choice(
                [-price_move_size, price_move_size]
            )
            fair_value += price_move

        # 2. Inventory-aware quote
        quote_centre = fair_value - k * inventory

        bid = quote_centre - half_spread
        ask = quote_centre + half_spread

        # 3. Probability that a customer trades
        trade_probability = (
            1 - spread_sensitivity * half_spread
        )

        trade_probability = max(
            0.05,
            min(0.95, trade_probability)
        )

        trade_draw = random.random()

        # 4. If a trade occurs
        if trade_draw < trade_probability:

            # Probability customer BUYS from us
            buy_probability = (
                0.5
                + customer_sensitivity
                * (fair_value - quote_centre)
            )

            buy_probability = max(
                0.05,
                min(0.95, buy_probability)
            )

            order_draw = random.random()

            if order_draw < buy_probability:
                order = "BUY"
            else:
                order = "SELL"

            # 5. Inventory-limit check
            if (
                order == "SELL"
                and inventory >= inventory_limit
            ):
                pass

            elif (
                order == "BUY"
                and inventory <= -inventory_limit
            ):
                pass

            else:
                # 6. Execute trade
                if order == "SELL":
                    execution_price = bid

                    cash -= execution_price
                    inventory += 1

                else:
                    execution_price = ask

                    cash += execution_price
                    inventory -= 1

        # 7. Track maximum inventory exposure
        max_abs_inventory = max(
            max_abs_inventory,
            abs(inventory)
        )

    # 8. Final mark-to-market PnL
    pnl = cash + inventory * fair_value

    return pnl, max_abs_inventory


def run_many_simulations(k, simulations=1000):
    pnls = []
    max_inventories = []

    for _ in range(simulations):
        pnl, max_inventory = run_simulation(k=k)

        pnls.append(pnl)
        max_inventories.append(max_inventory)

    average_pnl = sum(pnls) / len(pnls)

    average_max_inventory = (
        sum(max_inventories)
        / len(max_inventories)
    )

    worst_pnl = min(pnls)
    best_pnl = max(pnls)

    return {
        "average_pnl": average_pnl,
        "average_max_inventory": average_max_inventory,
        "worst_pnl": worst_pnl,
        "best_pnl": best_pnl,
    }


# ------------------------------
# Inventory-Aware Strategy
# ------------------------------

inventory_aware_results = run_many_simulations(
    k=0.25,
    simulations=1000
)

print("INVENTORY-AWARE STRATEGY")
print(
    "Average PnL:",
    round(
        inventory_aware_results["average_pnl"],
        2
    )
)
print(
    "Average Max Inventory:",
    round(
        inventory_aware_results[
            "average_max_inventory"
        ],
        2
    )
)
print(
    "Worst PnL:",
    round(
        inventory_aware_results["worst_pnl"],
        2
    )
)
print(
    "Best PnL:",
    round(
        inventory_aware_results["best_pnl"],
        2
    )
)


print()


# ------------------------------
# Baseline Strategy
# ------------------------------

baseline_results = run_many_simulations(
    k=0,
    simulations=1000
)

print("BASELINE STRATEGY")
print(
    "Average PnL:",
    round(
        baseline_results["average_pnl"],
        2
    )
)
print(
    "Average Max Inventory:",
    round(
        baseline_results[
            "average_max_inventory"
        ],
        2
    )
)
print(
    "Worst PnL:",
    round(
        baseline_results["worst_pnl"],
        2
    )
)
print(
    "Best PnL:",
    round(
        baseline_results["best_pnl"],
        2
    )
)