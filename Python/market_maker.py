import random
import statistics


# --------------------------------------------------
# GENERATE ONE RANDOM MARKET SCENARIO
# --------------------------------------------------

def generate_scenario(steps=20):
    """
    Generates the random components of one market scenario.

    These are generated separately from the strategy so that
    different strategies/parameters can face the exact same
    underlying randomness.
    """

    # Trade 1 begins with no price movement
    price_directions = [0]

    trade_draws = []
    order_draws = []

    for step in range(steps):

        # From Trade 2 onwards, fair value moves up or down
        if step > 0:
            price_directions.append(
                random.choice([-1, 1])
            )

        # Determines whether a customer trades
        trade_draws.append(
            random.random()
        )

        # Determines BUY vs SELL
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
    inventory_limit=5
):
    # Starting market parameters
    fair_value = 100
    half_spread = 1

    # Customer behaviour parameters
    customer_sensitivity = 0.2
    spread_sensitivity = 0.25

    # Starting market-maker position
    cash = 0
    inventory = 0

    # Risk statistics
    max_abs_inventory = 0
    rejected_trades = 0


    # --------------------------------------------------
    # RUN THROUGH EACH TRADING STEP
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
        # 3. PROBABILITY THAT CUSTOMER TRADES
        # ----------------------------------------------

        trade_probability = (
            1
            - spread_sensitivity
            * half_spread
        )

        # Keep probability valid
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
        # 4. CUSTOMER DECIDES WHETHER TO TRADE
        # ----------------------------------------------

        if trade_draw < trade_probability:

            # Probability that customer BUYS from us
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
            # 6. CHECK HARD INVENTORY LIMIT
            # ------------------------------------------

            # Customer SELL means we would BUY one more
            if (
                order == "SELL"
                and inventory >= inventory_limit
            ):
                rejected_trades += 1


            # Customer BUY means we would SELL one more
            elif (
                order == "BUY"
                and inventory <= -inventory_limit
            ):
                rejected_trades += 1


            # ------------------------------------------
            # 7. EXECUTE TRADE
            # ------------------------------------------

            else:

                # Customer SELLS to us
                if order == "SELL":

                    cash -= bid
                    inventory += 1


                # Customer BUYS from us
                else:

                    cash += ask
                    inventory -= 1


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
        rejected_trades
    )


# ==================================================
# DAY 24:
# REPEATED INVENTORY-LIMIT SENSITIVITY ANALYSIS
# ==================================================

simulations = 1000

inventory_limits = [
    2,
    3,
    5,
    10
]


# --------------------------------------------------
# GENERATE THE MARKET SCENARIOS ONCE
# --------------------------------------------------

scenarios = [
    generate_scenario()
    for _ in range(simulations)
]


# Store final results
limit_results = []


# --------------------------------------------------
# TEST EACH INVENTORY LIMIT
# --------------------------------------------------

for limit in inventory_limits:

    pnls = []
    max_inventories = []
    rejected_counts = []


    # Every limit sees EXACTLY the same scenarios
    for scenario in scenarios:

        (
            pnl,
            max_inventory,
            rejected
        ) = run_simulation(
            scenario=scenario,
            k=0.25,
            price_move_size=1,
            inventory_limit=limit
        )


        pnls.append(
            pnl
        )

        max_inventories.append(
            max_inventory
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


    # Sort PnLs so we can find downside percentile
    sorted_pnls = sorted(
        pnls
    )


    fifth_percentile = (
        sorted_pnls[
            int(
                0.05 * simulations
            )
        ]
    )


    # Save results for this limit
    limit_results.append({
        "limit": limit,

        "average_pnl":
            average_pnl,

        "pnl_std":
            pnl_std,

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
    "INVENTORY LIMIT SENSITIVITY RESULTS"
)

print()


print(
    f"{'Limit':<8}"
    f"{'Avg PnL':<12}"
    f"{'PnL SD':<12}"
    f"{'Avg Max Inv':<14}"
    f"{'Avg Reject':<14}"
    f"{'Loss %':<10}"
    f"{'5th % PnL':<12}"
)

print("-" * 82)


for result in limit_results:

    print(
        f"{result['limit']:<8}"
        f"{result['average_pnl']:<12.2f}"
        f"{result['pnl_std']:<12.2f}"
        f"{result['average_max_inventory']:<14.2f}"
        f"{result['average_rejected']:<14.2f}"
        f"{result['loss_probability'] * 100:<10.2f}"
        f"{result['fifth_percentile']:<12.2f}"
    )