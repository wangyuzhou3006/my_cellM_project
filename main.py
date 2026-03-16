import config
from model import run_simulation
from visualize import show_animation,plot_metrics

def main():
    history, history_grids = run_simulation(config)
    
    peak_heat = max(history["heat"])
    peak_sharing = max(history["sharing"])
    peak_heat_step = history["heat"].index(peak_heat)
    peak_depth = max(history["propagation_depth"])
    total_reached = history["cumulative_exposures"][-1]
    total_new_exposures = sum(history["new_exposures"])
    total_new_views = sum(history["new_views"])
    total_new_engagements = sum(history["new_engagements"])
    total_new_shares = sum(history["new_shares"])
    overall_view_conversion = total_new_views / max(total_new_exposures, 1)
    overall_engagement_rate = total_new_engagements / max(total_new_views, 1)
    overall_share_rate = total_new_shares / max(total_new_engagements, 1)
    
    print("Simulation Summary")
    print(f"Grid Size: {config.GRID_SIZE} x {config.GRID_SIZE}")
    print(f"Steps: {config.STEPS}")
    print(f"Peak Heat: {peak_heat:.2f}")
    print(f"Peak Heat Step: {peak_heat_step}")
    print(f"Peak sharing users: {peak_sharing}")
    print(f"Final reached users: {total_reached}")
    print(f"Exposure volume: {total_new_exposures}")
    print(f"Peak propagation depth: {peak_depth}")
    print(f"Overall view conversion rate: {overall_view_conversion:.2%}")
    print(f"Overall engagement rate: {overall_engagement_rate:.2%}")
    print(f"Overall share rate: {overall_share_rate:.2%}")
    
    plot_metrics(history)
    show_animation(history_grids, interval=config.INTERVAL)

if __name__ == "__main__":
    main()
