import csv
import random
import statistics
from pathlib import Path

try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None


#PROJECT SETTINGS

RANDOM_SEED = 42
SIMULATIONS = 10_000
STEPS = 20

STARTING_FAIR_VALUE = 100

DEFAULT_K = 0.25
DEFAULT_HALF_SPREAD = 1.0
DEFAULT_CUSTOMER_SENSITIVITY = 0.2
DEFAULT_SPREAD_SENSITIVITY = 0.25
DEFAULT_PRICE_MOVE_SIZE = 1.0
DEFAULT_INVENTORY_LIMIT = 5

#OUTPUT FOLDERS

PROJECT_ROOT = Path(__file__).resolve().parent.parent

RESULTS_DIR = PROJECT_ROOT / "04 Experiments"
FIGURES_DIR = PROJECT_ROOT / "05 Figures"

RESULTS_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR.mkdir(parents=True, exist_ok=True)


#HELPER FUNCTIONS


def clamp(value, lower, upper):
    """
    Restrict value to the interval [lower, upper].
    """
    return max(lower, min(upper, value))


def percentile(values, p):
    """
    Simple percentile calculation.
    p should be between 0 and 1.
    """
    ordered = sorted(values)

    index = int(
        p * (len(ordered) - 1)
    )

    return ordered[index]


def write_csv(filename, rows):
    """
    Save a list of dictionaries as a CSV file.
    """
    if not rows:
        return

    path = RESULTS_DIR / filename

    with open(
        path,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=rows[0].keys()
        )

        writer.writeheader()
        writer.writerows(rows)



#GENERATE RANDOM MARKET SCENARIO

def generate_scenario(
    rng,
    steps=STEPS
):
    """
    Generate one market scenario.

    Randomness is generated separately from the strategy so that
    different strategies can face exactly the same underlying
    market conditions.
    """

    price_directions = [0]
    trade_draws = []
    order_draws = []

    for step in range(steps):

        if step > 0:
            price_directions.append(
                rng.choice([-1, 1])
            )

        trade_draws.append(
            rng.random()
        )

        order_draws.append(
            rng.random()
        )

    return {
        "price_directions": price_directions,
        "trade_draws": trade_draws,
        "order_draws": order_draws,
    }


#RUN ONE MARKET-MAKING SIMULATION

def run_simulation(
    scenario,
    k=DEFAULT_K,
    half_spread=DEFAULT_HALF_SPREAD,
    customer_sensitivity=DEFAULT_CUSTOMER_SENSITIVITY,
    spread_sensitivity=DEFAULT_SPREAD_SENSITIVITY,
    price_move_size=DEFAULT_PRICE_MOVE_SIZE,
    inventory_limit=DEFAULT_INVENTORY_LIMIT,
    starting_fair_value=STARTING_FAIR_VALUE,
    record_path=False
):
    """
    Run one complete market-making simulation.
    """

    fair_value = starting_fair_value

    cash = 0.0
    inventory = 0

    max_abs_inventory = 0

    executed_trades = 0
    rejected_trades = 0
    no_trade_steps = 0

    path = []


    for step in range(STEPS):

        # FAIR VALUE MOVEMENT


        price_move = (
            scenario["price_directions"][step]
            * price_move_size
        )

        fair_value += price_move


        # ----------------------------------------------------
        # 2. INVENTORY-AWARE QUOTE
        # ----------------------------------------------------

        quote_centre = (
            fair_value
            - k * inventory
        )

        bid = (
            quote_centre
            - half_spread
        )

        ask = (
            quote_centre
            + half_spread
        )


        # ----------------------------------------------------
        # 3. PROBABILITY THAT A CUSTOMER TRADES
        # ----------------------------------------------------

        trade_probability = (
            1
            - spread_sensitivity
            * half_spread
        )

        trade_probability = clamp(
            trade_probability,
            0.05,
            0.95
        )


        # Default step status
        status = "NO TRADE"
        order = None


        # ----------------------------------------------------
        # 4. DOES A TRADE OCCUR?
        # ----------------------------------------------------

        if (
            scenario["trade_draws"][step]
            < trade_probability
        ):

            # ------------------------------------------------
            # 5. BUY / SELL DIRECTION
            # ------------------------------------------------

            buy_probability = (
                0.5
                + customer_sensitivity
                * (
                    fair_value
                    - quote_centre
                )
            )

            buy_probability = clamp(
                buy_probability,
                0.05,
                0.95
            )


            if (
                scenario["order_draws"][step]
                < buy_probability
            ):
                order = "BUY"

            else:
                order = "SELL"


            # ------------------------------------------------
            # 6. HARD INVENTORY LIMIT
            # ------------------------------------------------

            if (
                order == "SELL"
                and inventory >= inventory_limit
            ):

                status = "REJECTED"
                rejected_trades += 1


            elif (
                order == "BUY"
                and inventory <= -inventory_limit
            ):

                status = "REJECTED"
                rejected_trades += 1


            # ------------------------------------------------
            # 7. EXECUTE TRADE
            # ------------------------------------------------

            else:

                status = "EXECUTED"
                executed_trades += 1


                # Customer SELL:
                # market maker BUYS at bid
                if order == "SELL":

                    cash -= bid
                    inventory += 1


                # Customer BUY:
                # market maker SELLS at ask
                else:

                    cash += ask
                    inventory -= 1


        else:

            no_trade_steps += 1


        # ----------------------------------------------------
        # 8. INVENTORY RISK
        # ----------------------------------------------------

        max_abs_inventory = max(
            max_abs_inventory,
            abs(inventory)
        )


        # ----------------------------------------------------
        # 9. MARK-TO-MARKET PnL
        # ----------------------------------------------------

        pnl = (
            cash
            + inventory * fair_value
        )


        if record_path:

            path.append({
                "step": step + 1,
                "fair_value": fair_value,
                "inventory": inventory,
                "cash": cash,
                "pnl": pnl,
                "bid": bid,
                "ask": ask,
                "status": status,
                "order": order,
            })


    final_pnl = (
        cash
        + inventory * fair_value
    )


    return {
        "final_pnl": final_pnl,
        "final_inventory": inventory,
        "max_abs_inventory": max_abs_inventory,
        "executed_trades": executed_trades,
        "rejected_trades": rejected_trades,
        "no_trade_steps": no_trade_steps,
        "path": path,
    }


# ============================================================
# SUMMARY STATISTICS
# ============================================================

def summarise(results):

    pnls = [
        result["final_pnl"]
        for result in results
    ]

    max_inventories = [
        result["max_abs_inventory"]
        for result in results
    ]

    executed = [
        result["executed_trades"]
        for result in results
    ]

    rejected = [
        result["rejected_trades"]
        for result in results
    ]

    final_abs_inventory = [
        abs(result["final_inventory"])
        for result in results
    ]


    return {
        "average_pnl":
            statistics.mean(pnls),

        "median_pnl":
            statistics.median(pnls),

        "pnl_std":
            statistics.stdev(pnls),

        "loss_probability":
            sum(
                1
                for pnl in pnls
                if pnl < 0
            ) / len(pnls),

        "p5_pnl":
            percentile(
                pnls,
                0.05
            ),

        "average_max_inventory":
            statistics.mean(
                max_inventories
            ),

        "average_final_abs_inventory":
            statistics.mean(
                final_abs_inventory
            ),

        "average_executed_trades":
            statistics.mean(
                executed
            ),

        "average_rejected_trades":
            statistics.mean(
                rejected
            ),
    }


# ============================================================
# GENERATE FINAL COMMON SCENARIO BANK
# ============================================================

rng = random.Random(
    RANDOM_SEED
)

scenarios = [
    generate_scenario(rng)
    for _ in range(SIMULATIONS)
]


# ============================================================
# 1. CORE STRATEGY COMPARISON
# ============================================================

inventory_aware_results = [
    run_simulation(
        scenario,
        k=0.25
    )
    for scenario in scenarios
]


baseline_results = [
    run_simulation(
        scenario,
        k=0.0
    )
    for scenario in scenarios
]


ia_summary = summarise(
    inventory_aware_results
)

baseline_summary = summarise(
    baseline_results
)


core_rows = [
    {
        "strategy": "Inventory-Aware",
        "k": 0.25,
        **ia_summary,
    },

    {
        "strategy": "Baseline",
        "k": 0.0,
        **baseline_summary,
    }
]


write_csv(
    "core_strategy_comparison.csv",
    core_rows
)


# Paired differences
pnl_differences = [
    inventory_aware_results[i]["final_pnl"]
    - baseline_results[i]["final_pnl"]

    for i in range(SIMULATIONS)
]


inventory_differences = [
    inventory_aware_results[i]["max_abs_inventory"]
    - baseline_results[i]["max_abs_inventory"]

    for i in range(SIMULATIONS)
]


print()
print("CORE STRATEGY COMPARISON")
print()

for row in core_rows:

    print(row["strategy"])

    print(
        "Average PnL:",
        round(row["average_pnl"], 3)
    )

    print(
        "PnL SD:",
        round(row["pnl_std"], 3)
    )

    print(
        "Loss Probability:",
        round(
            row["loss_probability"] * 100,
            2
        ),
        "%"
    )

    print(
        "5th Percentile PnL:",
        round(row["p5_pnl"], 3)
    )

    print(
        "Average Max Inventory:",
        round(
            row["average_max_inventory"],
            3
        )
    )

    print()


print(
    "Average paired PnL difference (IA - Baseline):",
    round(
        statistics.mean(
            pnl_differences
        ),
        3
    )
)

print(
    "Average paired inventory difference (IA - Baseline):",
    round(
        statistics.mean(
            inventory_differences
        ),
        3
    )
)


# ============================================================
# GENERIC SENSITIVITY FUNCTION
# ============================================================

def run_sensitivity(
    parameter_name,
    parameter_values,
    fixed_parameters=None
):

    if fixed_parameters is None:
        fixed_parameters = {}

    rows = []


    for value in parameter_values:

        parameters = dict(
            fixed_parameters
        )

        parameters[
            parameter_name
        ] = value


        results = [
            run_simulation(
                scenario,
                **parameters
            )

            for scenario in scenarios
        ]


        summary = summarise(
            results
        )


        row = {
            parameter_name: value,
            **summary,
        }

        rows.append(
            row
        )


    return rows


# ============================================================
# 2. INVENTORY SENSITIVITY
# ============================================================

inventory_sensitivity = run_sensitivity(
    parameter_name="k",

    parameter_values=[
        0,
        0.1,
        0.25,
        0.5,
        1.0
    ]
)


write_csv(
    "inventory_sensitivity.csv",
    inventory_sensitivity
)


# ============================================================
# 3. VOLATILITY SENSITIVITY
# ============================================================

volatility_sensitivity = run_sensitivity(
    parameter_name="price_move_size",

    parameter_values=[
        0.5,
        1.0,
        2.0,
        3.0
    ],

    fixed_parameters={
        "k": 0.25
    }
)


write_csv(
    "volatility_sensitivity.csv",
    volatility_sensitivity
)


# ============================================================
# 4. INVENTORY-LIMIT SENSITIVITY
# ============================================================

inventory_limit_sensitivity = run_sensitivity(
    parameter_name="inventory_limit",

    parameter_values=[
        2,
        3,
        5,
        10
    ],

    fixed_parameters={
        "k": 0.25
    }
)


write_csv(
    "inventory_limit_sensitivity.csv",
    inventory_limit_sensitivity
)


# ============================================================
# 5. SPREAD SENSITIVITY
# ============================================================

spread_sensitivity_results = run_sensitivity(
    parameter_name="half_spread",

    parameter_values=[
        0.5,
        1.0,
        1.5,
        2.0
    ],

    fixed_parameters={
        "k": 0.25
    }
)


write_csv(
    "spread_sensitivity.csv",
    spread_sensitivity_results
)


# ============================================================
# PRINT SENSITIVITY TABLES
# ============================================================

def print_sensitivity(
    title,
    rows,
    parameter
):

    print()
    print(title)
    print()

    print(
        f"{parameter:<18}"
        f"{'Avg PnL':<12}"
        f"{'PnL SD':<12}"
        f"{'Loss %':<12}"
        f"{'5th % PnL':<14}"
        f"{'Avg Max Inv':<14}"
        f"{'Avg Trades':<12}"
    )

    print("-" * 94)


    for row in rows:

        print(
            f"{row[parameter]:<18.2f}"
            f"{row['average_pnl']:<12.2f}"
            f"{row['pnl_std']:<12.2f}"
            f"{row['loss_probability'] * 100:<12.2f}"
            f"{row['p5_pnl']:<14.2f}"
            f"{row['average_max_inventory']:<14.2f}"
            f"{row['average_executed_trades']:<12.2f}"
        )


print_sensitivity(
    "INVENTORY SENSITIVITY",
    inventory_sensitivity,
    "k"
)

print_sensitivity(
    "VOLATILITY SENSITIVITY",
    volatility_sensitivity,
    "price_move_size"
)

print_sensitivity(
    "INVENTORY LIMIT SENSITIVITY",
    inventory_limit_sensitivity,
    "inventory_limit"
)

print_sensitivity(
    "SPREAD SENSITIVITY",
    spread_sensitivity_results,
    "half_spread"
)


# ============================================================
# FIGURES
# ============================================================

if plt is not None:

    # --------------------------------------------------------
    # Figure 1: PnL Distribution
    # --------------------------------------------------------

    ia_pnls = [
        result["final_pnl"]
        for result in inventory_aware_results
    ]

    baseline_pnls = [
        result["final_pnl"]
        for result in baseline_results
    ]


    plt.figure()

    plt.hist(
        ia_pnls,
        bins=40,
        alpha=0.5,
        label="Inventory-Aware"
    )

    plt.hist(
        baseline_pnls,
        bins=40,
        alpha=0.5,
        label="Baseline"
    )

    plt.xlabel(
        "Final PnL"
    )

    plt.ylabel(
        "Frequency"
    )

    plt.title(
        "Distribution of Final PnL"
    )

    plt.legend()

    plt.tight_layout()

    plt.savefig(
        FIGURES_DIR
        / "pnl_distribution.png",

        dpi=300
    )

    plt.close()


    # --------------------------------------------------------
    # Figure 2: k vs PnL
    # --------------------------------------------------------

    plt.figure()

    plt.plot(
        [
            row["k"]
            for row in inventory_sensitivity
        ],

        [
            row["average_pnl"]
            for row in inventory_sensitivity
        ],

        marker="o"
    )

    plt.xlabel(
        "Inventory Sensitivity k"
    )

    plt.ylabel(
        "Average PnL"
    )

    plt.title(
        "Average PnL vs Inventory Sensitivity"
    )

    plt.tight_layout()

    plt.savefig(
        FIGURES_DIR
        / "inventory_sensitivity_pnl.png",

        dpi=300
    )

    plt.close()


    # --------------------------------------------------------
    # Figure 3: k vs Inventory
    # --------------------------------------------------------

    plt.figure()

    plt.plot(
        [
            row["k"]
            for row in inventory_sensitivity
        ],

        [
            row["average_max_inventory"]
            for row in inventory_sensitivity
        ],

        marker="o"
    )

    plt.xlabel(
        "Inventory Sensitivity k"
    )

    plt.ylabel(
        "Average Maximum Absolute Inventory"
    )

    plt.title(
        "Inventory Exposure vs Inventory Sensitivity"
    )

    plt.tight_layout()

    plt.savefig(
        FIGURES_DIR
        / "inventory_sensitivity_risk.png",

        dpi=300
    )

    plt.close()


    # --------------------------------------------------------
    # Figure 4: Volatility vs PnL Risk
    # --------------------------------------------------------

    plt.figure()

    plt.plot(
        [
            row["price_move_size"]
            for row in volatility_sensitivity
        ],

        [
            row["pnl_std"]
            for row in volatility_sensitivity
        ],

        marker="o"
    )

    plt.xlabel(
        "Price Move Size"
    )

    plt.ylabel(
        "PnL Standard Deviation"
    )

    plt.title(
        "PnL Risk vs Price Volatility"
    )

    plt.tight_layout()

    plt.savefig(
        FIGURES_DIR
        / "volatility_pnl_risk.png",

        dpi=300
    )

    plt.close()


    # --------------------------------------------------------
    # Figure 5: Inventory Limit vs Rejections
    # --------------------------------------------------------

    plt.figure()

    plt.plot(
        [
            row["inventory_limit"]
            for row in inventory_limit_sensitivity
        ],

        [
            row["average_rejected_trades"]
            for row in inventory_limit_sensitivity
        ],

        marker="o"
    )

    plt.xlabel(
        "Inventory Limit"
    )

    plt.ylabel(
        "Average Rejected Trades"
    )

    plt.title(
        "Rejected Trades vs Inventory Limit"
    )

    plt.tight_layout()

    plt.savefig(
        FIGURES_DIR
        / "inventory_limit_rejections.png",

        dpi=300
    )

    plt.close()


    # --------------------------------------------------------
    # Figure 6: Spread vs Trade Frequency
    # --------------------------------------------------------

    plt.figure()

    plt.plot(
        [
            row["half_spread"]
            for row in spread_sensitivity_results
        ],

        [
            row["average_executed_trades"]
            for row in spread_sensitivity_results
        ],

        marker="o"
    )

    plt.xlabel(
        "Half Spread"
    )

    plt.ylabel(
        "Average Executed Trades"
    )

    plt.title(
        "Trade Frequency vs Spread Width"
    )

    plt.tight_layout()

    plt.savefig(
        FIGURES_DIR
        / "spread_trade_frequency.png",

        dpi=300
    )

    plt.close()


    # --------------------------------------------------------
    # Figure 7: Spread vs PnL
    # --------------------------------------------------------

    plt.figure()

    plt.plot(
        [
            row["half_spread"]
            for row in spread_sensitivity_results
        ],

        [
            row["average_pnl"]
            for row in spread_sensitivity_results
        ],

        marker="o"
    )

    plt.xlabel(
        "Half Spread"
    )

    plt.ylabel(
        "Average PnL"
    )

    plt.title(
        "Average PnL vs Spread Width"
    )

    plt.tight_layout()

    plt.savefig(
        FIGURES_DIR
        / "spread_pnl.png",

        dpi=300
    )

    plt.close()


    print()
    print(
        "Figures saved to:",
        FIGURES_DIR
    )

else:

    print()
    print(
        "matplotlib is not installed."
    )

    print(
        "CSV results were still generated successfully."
    )


print()
print(
    "Results saved to:",
    RESULTS_DIR
)

print()
print(
    "FINAL PROJECT SIMULATION COMPLETE"
)