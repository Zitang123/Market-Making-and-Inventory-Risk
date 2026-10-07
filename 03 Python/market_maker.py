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
