import random
import statistics
import matplotlib.pyplot as plt

def generate_scenario(steps=20, price_move_size=1):
    price_moves = [0]
    trade_draws = []
    order_draws = []

    for step in range(steps):
        if step > 0:
            price_moves.append(
                random.choice(
                    [-price_move_size, price_move_size]
                )
            )

        trade_draws.append(random.random())
        order_draws.append(random.random())

    return {
        "price_moves": price_moves,
        "trade_draws": trade_draws,
        "order_draws": order_draws,
    }


def run_simulation(
    scenario,
    k=0.25,
    steps=20
):
    fair_value = 100
    half_spread = 1

    customer_sensitivity = 0.2
    spread_sensitivity = 0.25

    inventory_limit = 5

    cash = 0
    inventory = 0
    max_abs_inventory = 0

    for trade in range(1, steps + 1):

        # 1. Fair value movement
        price_move = (
            scenario["price_moves"][trade - 1]
        )

        fair_value += price_move

        # 2. Inventory-aware quote
        quote_centre = (
            fair_value - k * inventory
        )

        bid = quote_centre - half_spread
        ask = quote_centre + half_spread

        # 3. Probability a customer trades
        trade_probability = (
            1
            - spread_sensitivity
            * half_spread
        )

        trade_probability = max(
            0.05,
            min(0.95, trade_probability)
        )

        trade_draw = (
            scenario["trade_draws"][trade - 1]
        )

        # 4. Customer trades
        if trade_draw < trade_probability:

            buy_probability = (
                0.5
                + customer_sensitivity
                * (fair_value - quote_centre)
            )

            buy_probability = max(
                0.05,
                min(0.95, buy_probability)
            )

            order_draw = (
                scenario["order_draws"][trade - 1]
            )

            if order_draw < buy_probability:
                order = "BUY"
            else:
                order = "SELL"

            # 5. Hard inventory limit
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
                # 6. Execute
                if order == "SELL":
                    cash -= bid
                    inventory += 1

                else:
                    cash += ask
                    inventory -= 1

        # 7. Inventory-risk tracking
        max_abs_inventory = max(
            max_abs_inventory,
            abs(inventory)
        )

    pnl = cash + inventory * fair_value

    return pnl, max_abs_inventory


# ------------------------------------
# Paired simulations
# ------------------------------------

simulations = 1000

ia_pnls = []
baseline_pnls = []

ia_max_inventories = []
baseline_max_inventories = []

for _ in range(simulations):

    # ONE scenario shared by both strategies
    scenario = generate_scenario()

    ia_pnl, ia_max_inventory = (
        run_simulation(
            scenario=scenario,
            k=0.25
        )
    )

    baseline_pnl, baseline_max_inventory = (
        run_simulation(
            scenario=scenario,
            k=0
        )
    )

    ia_pnls.append(ia_pnl)
    baseline_pnls.append(baseline_pnl)

    ia_max_inventories.append(
        ia_max_inventory
    )

    baseline_max_inventories.append(
        baseline_max_inventory
    )


# ------------------------------------
# Summary statistics
# ------------------------------------

average_ia_pnl = (
    sum(ia_pnls) / simulations
)

average_baseline_pnl = (
    sum(baseline_pnls) / simulations
)

average_ia_inventory = (
    sum(ia_max_inventories)
    / simulations
)

average_baseline_inventory = (
    sum(baseline_max_inventories)
    / simulations
)


pnl_differences = [
    ia_pnls[i] - baseline_pnls[i]
    for i in range(simulations)
]

inventory_differences = [
    ia_max_inventories[i]
    - baseline_max_inventories[i]
    for i in range(simulations)
]


average_pnl_difference = (
    sum(pnl_differences)
    / simulations
)

average_inventory_difference = (
    sum(inventory_differences)
    / simulations
)


ia_pnl_wins = sum(
    1
    for diff in pnl_differences
    if diff > 0
)

ia_inventory_wins = sum(
    1
    for diff in inventory_differences
    if diff < 0
)

ia_std = statistics.stdev(ia_pnls)
baseline_std = statistics.stdev(baseline_pnls)

ia_median = statistics.median(ia_pnls)
baseline_median = statistics.median(baseline_pnls)

ia_loss_probability = (
    sum(1 for pnl in ia_pnls if pnl < 0)
    / simulations
)

baseline_loss_probability = (
    sum(1 for pnl in baseline_pnls if pnl < 0)
    / simulations 
)


sorted_ia = sorted(ia_pnls)
sorted_baseline = sorted(baseline_pnls)

index_5 = int(0.05 * simulations)

ia_5th_percentile = sorted_ia[index_5]
baseline_5th_percentile = sorted_baseline[index_5]

print("PAIRED SIMULATION RESULTS")
print()

print("Inventory-Aware Average PnL:")
print(round(average_ia_pnl, 2))

print("Baseline Average PnL:")
print(round(average_baseline_pnl, 2))

print()

print("Inventory-Aware Average Max Inventory:")
print(round(average_ia_inventory, 2))

print("Baseline Average Max Inventory:")
print(round(average_baseline_inventory, 2))

print()

print(
    "Average PnL Difference (IA - Baseline):",
    round(average_pnl_difference, 2)
)

print(
    "Average Max Inventory Difference (IA - Baseline):",
    round(average_inventory_difference, 2)
)

print()

print(
    "IA Higher PnL:",
    ia_pnl_wins,
    "/",
    simulations
)

print(
    "IA Lower Max Inventory:",
    ia_inventory_wins,
    "/",
    simulations
)



print()
print("RISK STATISTICS")
print()

print("Inventory-Aware")
print("Median PnL:", round(ia_median, 2))
print("PnL Standard Deviation:", round(ia_std, 2))
print(
    "Probability of Loss:",
    round(ia_loss_probability * 100, 2),
    "%"
)
print(
    "5th Percentile PnL:",
    round(ia_5th_percentile, 2)
)

print()

print("Baseline")
print("Median PnL:", round(baseline_median, 2))
print(
    "PnL Standard Deviation:",
    round(baseline_std, 2)
)
print(
    "Probability of Loss:",
    round(baseline_loss_probability * 100, 2),
    "%"
)
print(
    "5th Percentile PnL:",
    round(baseline_5th_percentile, 2)
)

plt.hist(
    ia_pnls,
    bins = 30,
    alpha = 0.5,
    label = "Inventory-Aware"
)

plt.hist(
    baseline_pnls,
    bins=30,
    alpha=0.5,
    label = "Baseline"
)

plt.xlabel("Final PnL")
plt.ylabel("Frequency")
plt.title("Distribution of Final PnL")
plt.legend()

plt.show()