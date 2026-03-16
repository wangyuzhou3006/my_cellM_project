import config
from model import run_simulation
from visualize import show_animation,plot_metrics

def main():
    history, history_grids = run_simulation(config)
    
    peak_heat = max(history["heat"])
    peak_sharing = max(history["sharing"])
    peak_heat_step = history["heat"].index(peak_heat)
    peak_depth = max(history["max_social_depth"])
    total_reached = history["cumulative_exposures"][-1]
    total_new_exposures = history["cumulative_exposures"][-1] - config.INITIAL_SHARERS
    cumulative_views = history["cumulative_views"][-1]
    cumulative_engagements = history["cumulative_engagements"][-1]
    cumulative_shares = history["cumulative_shares"][-1]
    total_recommended_reach = history["current_recommended_reach"][-1]
    overall_view_conversion = cumulative_views / max(total_new_exposures, 1)
    overall_engagement_rate = cumulative_engagements / max(cumulative_views, 1)
    overall_share_rate = cumulative_shares / max(cumulative_engagements, 1)
    overall_skip_rate = sum(history["new_skips"]) / max(total_new_exposures, 1)
    overall_view_drop_rate = sum(history["new_drop_view"]) / max(cumulative_views, 1)
    overall_engage_drop_rate = sum(history["new_drop_engage"]) / max(cumulative_engagements, 1)
    
    print("Simulation Summary")
    print(f"Grid Size: {config.GRID_SIZE} x {config.GRID_SIZE}")
    print(f"Steps: {config.STEPS}")
    print(f"Peak Heat: {peak_heat:.2f}")
    print(f"Peak Heat Step: {peak_heat_step}")
    print(f"Peak sharing users: {peak_sharing}")
    print(f"Final reached users: {total_reached}")
    print(f"Exposure volume: {total_new_exposures}")
    print(f"Recommended reach: {total_recommended_reach}")
    print(f"Peak propagation depth: {peak_depth}")
    print(f"Overall view conversion rate: {overall_view_conversion:.2%}")
    print(f"Overall engagement rate: {overall_engagement_rate:.2%}")
    print(f"Overall share rate: {overall_share_rate:.2%}")
    print(f"Overall skip rate: {overall_skip_rate:.2%}")
    print(f"Overall view drop rate: {overall_view_drop_rate:.2%}")
    print(f"Overall engage drop rate: {overall_engage_drop_rate:.2%}")
    
    plot_metrics(history)
    show_animation(history_grids, interval=config.INTERVAL)

if __name__ == "__main__":
    main()
