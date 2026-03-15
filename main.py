import config
from model import run_simulation
from visualize import show_animation,plot_metrics

def main():
    history, history_grids = run_simulation(config)
    
    peak_heat = max(history["heat"])
    peak_sharing = max(history["sharing"])
    total_viewed = history["viewed"][-1] + history["sharing"][-1] + history["inactive"][-1]
    
    print("Simulation Summary")
    print(f"Grid Size: {config.GRID_SIZE} x {config.GRID_SIZE}")
    print(f"Steps: {config.STEPS}")
    print(f"Peak Heat: {peak_heat:.2f}")
    print(f"Peak sharing users: {peak_sharing}")
    print(f"Final reached users: {total_viewed}")
    
    plot_metrics(history)
    show_animation(history_grids, interval=config.INTERVAL)

if __name__ == "__main__":
    main()