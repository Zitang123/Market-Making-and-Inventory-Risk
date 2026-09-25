import random
import statistics


# --------------------------------------------------
# GENERATE ONE RANDOM MARKET SCENARIO
# --------------------------------------------------

def generate_scenario(steps=20):
    """
    Generate the random components of one market scenario.

    We generate randomness separately from the strategy so that
    every parameter setting can face exactly the same scenarios.
    """

    price_directions = [0]
    trade_draws = []
    order_draws = []

    for step in range(steps):

        if step > 0:
            price_directions.append(
                random.choice([-1, 1])
            )

        trade_draws.append(
            random.random()
        )

        order_draws.append(
            random.random()
        )

    return {
        "price_directions": price_directions,
        "trade_draws": trade_draws,
        "order_draws": order_draws,
    }


# --------------------------------------------------
# RUN ONE MARKET-MAKING SIMULATION
# --------------------------------------------------

def run_simulation(
    scenario,
    k=0.25,
    steps=20,
    price_move_size=1,
    inventory_limit=5,
    half_spread=1
):
    # Starting market state
    fair_value = 100

    # Customer behaviour parameters
    customer_sensitivity = 0.2
    spread_sensitivity = 0.25

    # Market-maker state
    cash = 0
    inventory = 0

    # Risk / activity tracking
    max_abs_inventory = 0
    rejected_trades = 0
    executed_trades = 0


    # --------------------------------------------------
    # RUN THROUGH EACH STEP
    # --------------------------------------------------

    for trade in range(1, steps + 1):

        # ----------------------------------------------
        # 1. FAIR VALUE MOVEMENT
        # ----------------------------------------------

        price_direction = (
            scenario["price_directions"][trade - 1]
        )

        price_move = (
            price_direction * price_move_size
        )

        fair_value += price_move


        # ----------------------------------------------
        # 2. INVENTORY-AWARE QUOTING
        # ----------------------------------------------

        quote_centre = (
            fair_value - k * inventory
        )

        bid = (
            quote_centre - half_spread
        )

        ask = (
            quote_centre + half_spread
        )


        # ----------------------------------------------
        # 3. TRADE PROBABILITY
        # ----------------------------------------------

        trade_probability = (
            1
            - spread_sensitivity * half_spread
        )

        # Restrict to a valid probability range
        trade_probability = max(
            0.05,
            min(
                0.95,
                trade_probability
            )
        )

        trade_draw = (
            scenario["trade_draws"][trade - 1]
        )


        # ----------------------------------------------
        # 4. DOES A CUSTOMER TRADE?
        # ----------------------------------------------

        if trade_draw < trade_probability:

            # Probability customer BUYS from us
            buy_probability = (
                0.5
                + customer_sensitivity
                * (fair_value - quote_centre)
            )

            buy_probability = max(
                0.05,
                min(
                    0.95,
                    buy_probability
                )
            )

            order_draw = (
                scenario["order_draws"][trade - 1]
            )


            # ------------------------------------------
            # 5. BUY OR SELL?
            # ------------------------------------------

            if order_draw < buy_probability:
                order = "BUY"

            else:
                order = "SELL"


            # ------------------------------------------
            # 6. INVENTORY-LIMIT CHECK
            # ------------------------------------------

            # Customer SELL means we BUY one more unit
            if (
                order == "SELL"
                and inventory >= inventory_limit
            ):
                rejected_trades += 1


            # Customer BUY means we SELL one more unit
            elif (
                order == "BUY"
                and inventory <= -inventory_limit
            ):
                rejected_trades += 1


            # ------------------------------------------
            # 7. EXECUTE TRADE
            # ------------------------------------------

            else:

                if order == "SELL":
                    cash -= bid
                    inventory += 1
                    executed_trades += 1

                else:
                    cash += ask
                    inventory -= 1
                    executed_trades += 1


        # ----------------------------------------------
        # 8. TRACK MAXIMUM INVENTORY EXPOSURE
        # ----------------------------------------------

        max_abs_inventory = max(
            max_abs_inventory,
            abs(inventory)
        )


    # --------------------------------------------------
    # FINAL MARK-TO-MARKET PnL
    # --------------------------------------------------

    pnl = (
        cash
        + inventory * fair_value
    )


    return (
        pnl,
        max_abs_inventory,
        rejected_trades,
        executed_trades
    )


# ==================================================
# DAY 25:
# REPEATED SPREAD SENSITIVITY ANALYSIS
# ==================================================

simulations = 1000

half_spreads = [
    0.5,
    1.0,
    1.5,
    2.0
]


# --------------------------------------------------
# GENERATE SCENARIOS ONCE
# --------------------------------------------------

scenarios = [
    generate_scenario()
    for _ in range(simulations)
]


spread_results = []


# --------------------------------------------------
# TEST EACH HALF-SPREAD
# --------------------------------------------------

for half_spread in half_spreads:

    pnls = []
    max_inventories = []
    executed_counts = []
    rejected_counts = []


    # Every spread sees the SAME scenarios
    for scenario in scenarios:

        (
            pnl,
            max_inventory,
            rejected,
            executed
        ) = run_simulation(
            scenario=scenario,
            k=0.25,
            price_move_size=1,
            inventory_limit=5,
            half_spread=half_spread
        )


        pnls.append(
            pnl
        )

        max_inventories.append(
            max_inventory
        )

        executed_counts.append(
            executed
        )

        rejected_counts.append(
            rejected
        )


    # --------------------------------------------------
    # SUMMARY STATISTICS
    # --------------------------------------------------

    average_pnl = (
        sum(pnls)
        / simulations
    )


    pnl_std = statistics.stdev(
        pnls
    )


    average_max_inventory = (
        sum(max_inventories)
        / simulations
    )


    average_executed = (
        sum(executed_counts)
        / simulations
    )


    average_rejected = (
        sum(rejected_counts)
        / simulations
    )


    loss_probability = (
        sum(
            1
            for pnl in pnls
            if pnl < 0
        )
        / simulations
    )


    sorted_pnls = sorted(
        pnls
    )


    fifth_percentile = (
        sorted_pnls[
            int(0.05 * simulations)
        ]
    )


    spread_results.append({
        "half_spread":
            half_spread,

        "full_spread":
            2 * half_spread,

        "average_pnl":
            average_pnl,

        "pnl_std":
            pnl_std,

        "average_executed":
            average_executed,

        "average_max_inventory":
            average_max_inventory,

        "average_rejected":
            average_rejected,

        "loss_probability":
            loss_probability,

        "fifth_percentile":
            fifth_percentile,
    })


# ==================================================
# PRINT RESULTS
# ==================================================

print()

print(
    "SPREAD SENSITIVITY RESULTS"
)

print()


print(
    f"{'h':<8}"
    f"{'Spread':<10}"
    f"{'Avg PnL':<12}"
    f"{'PnL SD':<12}"
    f"{'Avg Trades':<12}"
    f"{'Avg Max Inv':<14}"
    f"{'Avg Reject':<12}"
    f"{'Loss %':<10}"
    f"{'5th % PnL':<12}"
)

print("-" * 100)


for result in spread_results:

    print(
        f"{result['half_spread']:<8.2f}"
        f"{result['full_spread']:<10.2f}"
        f"{result['average_pnl']:<12.2f}"
        f"{result['pnl_std']:<12.2f}"
        f"{result['average_executed']:<12.2f}"
        f"{result['average_max_inventory']:<14.2f}"
        f"{result['average_rejected']:<12.2f}"
        f"{result['loss_probability'] * 100:<10.2f}"
        f"{result['fifth_percentile']:<12.2f}"
    )