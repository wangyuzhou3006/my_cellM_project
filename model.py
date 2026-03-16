import numpy as np

UNSEEN = 0
EXPOSED = 1
VIEWED = 2
ENGAGED = 3
SHARING = 4
INACTIVE = 5

SOURCE_NONE = 0
SOURCE_SOCIAL = 1
SOURCE_RECOMMEND = 2


def creat_grid(size: int, initial_sharers: int, rng: np.random.Generator) -> np.ndarray:
    grid = np.zeros((size, size), dtype=np.int8)
    indices = rng.choice(size * size, size=initial_sharers, replace=False)
    rows, cols = np.unravel_index(indices, (size, size))
    grid[rows, cols] = SHARING
    return grid


def clip_grob(x):
    return np.clip(x, 0.0, 1.0)


def trait_multiplier(trait: np.ndarray, weight: float) -> np.ndarray:
    return 1.0 - weight + weight * trait


def sample_user_traits(config, rng: np.random.Generator, shape: tuple[int, int]) -> dict:
    activity = clip_grob(rng.normal(config.ACTIVITY_MEAN, config.ACTIVITY_STD, size=shape))
    interest = clip_grob(rng.normal(config.INTEREST_MEAN, config.INTEREST_STD, size=shape))
    influence = np.clip(
        rng.normal(config.INFLUENCE_MEAN, config.INFLUENCE_STD, size=shape),
        config.INFLUENCE_MIN,
        None,
    )
    fatigue_threshold = rng.integers(
        config.FATIGUE_THRESHOLD_MIN,
        config.FATIGUE_THRESHOLD_MAX + 1,
        size=shape,
    ).astype(np.int16)
    return {
        "activity": activity,
        "interest": interest,
        "influence": influence,
        "fatigue_threshold": fatigue_threshold,
    }


def get_neighbor_values(values: np.ndarray, mode: str = "moore") -> np.ndarray:
    padded = np.pad(values, 1, mode="constant", constant_values=0)

    up = padded[:-2, 1:-1]
    down = padded[2:, 1:-1]
    left = padded[1:-1, :-2]
    right = padded[1:-1, 2:]

    if mode == "von_neumann":
        return up + down + left + right

    if mode == "moore":
        up_left = padded[:-2, :-2]
        up_right = padded[:-2, 2:]
        down_left = padded[2:, :-2]
        down_right = padded[2:, 2:]
        return up + down + left + right + up_left + up_right + down_left + down_right

    raise ValueError(f"Unsupported neighborhood mode: {mode}")


def get_neighbor_count(grid: np.ndarray, state: int, mode: str = "moore") -> np.ndarray:
    return get_neighbor_values((grid == state).astype(np.int8), mode)


def get_neighbor_max(values: np.ndarray, mode: str = "moore") -> np.ndarray:
    padded = np.pad(values, 1, mode="constant", constant_values=-1)
    neighbors = [
        padded[:-2, 1:-1],
        padded[2:, 1:-1],
        padded[1:-1, :-2],
        padded[1:-1, 2:],
    ]

    if mode == "moore":
        neighbors.extend([
            padded[:-2, :-2],
            padded[:-2, 2:],
            padded[2:, :-2],
            padded[2:, 2:],
        ])
    elif mode != "von_neumann":
        raise ValueError(f"Unsupported neighborhood mode: {mode}")

    return np.maximum.reduce(neighbors)


def compute_heat(
    prev_heat: float,
    sharers: int,
    new_shares: int,
    heat_decay: float,
    heat_from_sharers: float,
    heat_from_new_shares: float,
) -> float:
    return heat_decay * prev_heat + heat_from_sharers * sharers + heat_from_new_shares * new_shares


def resolve_stage_transitions(
    mask: np.ndarray,
    forward_prob: np.ndarray,
    drop_prob: np.ndarray,
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray]:
    forward_prob = clip_grob(forward_prob)
    drop_prob = clip_grob(drop_prob)
    total_prob = forward_prob + drop_prob
    scale = np.maximum(total_prob, 1.0)
    forward_prob = forward_prob / scale
    drop_prob = drop_prob / scale

    rand = rng.random(mask.shape)
    forward_mask = mask & (rand < forward_prob)
    drop_mask = mask & (rand >= forward_prob) & (rand < forward_prob + drop_prob)
    return forward_mask, drop_mask


def count_states(grid: np.ndarray) -> dict:
    return {
        "unseen": int(np.sum(grid == UNSEEN)),
        "exposed": int(np.sum(grid == EXPOSED)),
        "viewed": int(np.sum(grid == VIEWED)),
        "engaged": int(np.sum(grid == ENGAGED)),
        "sharing": int(np.sum(grid == SHARING)),
        "inactive": int(np.sum(grid == INACTIVE)),
    }


def step(
    grid: np.ndarray,
    sharing_time: np.ndarray,
    social_depth_grid: np.ndarray,
    source_grid: np.ndarray,
    traits: dict,
    heat: float,
    rng: np.random.Generator,
    config,
):
    new_grid = grid.copy()
    new_sharing_time = sharing_time.copy()
    new_social_depth = social_depth_grid.copy()
    new_source_grid = source_grid.copy()

    activity = traits["activity"]
    interest = traits["interest"]
    influence = traits["influence"]
    fatigue_threshold = traits["fatigue_threshold"]

    sharing_neighbors = get_neighbor_count(grid, SHARING, config.NEIGHBORHOOD)
    sharing_influence = get_neighbor_values(
        np.where(grid == SHARING, influence, 0.0),
        config.NEIGHBORHOOD,
    )
    neighbor_social_depth = get_neighbor_max(
        np.where(grid == SHARING, social_depth_grid, -1),
        config.NEIGHBORHOOD,
    )

    # UNSEEN -> EXPOSED
    unseen_mask = grid == UNSEEN
    social_expose_prob = 1.0 - (1.0 - config.P_EXPOSE) ** sharing_influence
    social_expose_prob = clip_grob(
        social_expose_prob
        * trait_multiplier(activity, config.EXPOSE_ACTIVITY_WEIGHT)
        * trait_multiplier(interest, config.EXPOSE_INTEREST_WEIGHT)
        + config.HEAT_BOOST_EXPOSE * heat
    )
    recommend_expose_prob = clip_grob(
        (config.P_RECOMMEND + config.HEAT_BOOST_RECOMMEND * heat)
        * trait_multiplier(activity, config.RECOMMEND_ACTIVITY_WEIGHT)
        * trait_multiplier(interest, config.RECOMMEND_INTEREST_WEIGHT)
    )

    social_rand = rng.random(grid.shape)
    recommend_rand = rng.random(grid.shape)
    social_hits = unseen_mask & (social_rand < social_expose_prob)
    recommend_hits = unseen_mask & (recommend_rand < recommend_expose_prob)
    new_exposed = social_hits | recommend_hits

    new_grid[new_exposed] = EXPOSED
    social_first = new_exposed & social_hits
    recommend_first = new_exposed & ~social_hits
    new_source_grid[social_first] = SOURCE_SOCIAL
    new_source_grid[recommend_first] = SOURCE_RECOMMEND
    social_depth_mask = social_first & (neighbor_social_depth >= 0)
    new_social_depth[social_depth_mask] = neighbor_social_depth[social_depth_mask] + 1

    # EXPOSED -> VIEWED | INACTIVE
    exposed_mask = grid == EXPOSED
    view_prob = (
        config.P_VIEW
        + config.NEIGHBOR_VIEW_BOOST * sharing_influence
        + config.HEAT_BOOST_VIEW * heat
    )
    view_prob = clip_grob(
        view_prob
        * trait_multiplier(activity, config.VIEW_ACTIVITY_WEIGHT)
        * trait_multiplier(interest, config.VIEW_INTEREST_WEIGHT)
    )
    skip_prob = (
        config.P_SKIP
        + config.INTEREST_DROP_WEIGHT * (1.0 - interest)
        + config.ACTIVITY_DROP_WEIGHT * (1.0 - activity)
    )
    skip_prob = clip_grob(skip_prob / (1.0 + config.HEAT_PROTECT_VIEW * heat))
    exposed_to_viewed, exposed_to_inactive = resolve_stage_transitions(
        exposed_mask,
        view_prob,
        skip_prob,
        rng,
    )
    new_grid[exposed_to_viewed] = VIEWED
    new_grid[exposed_to_inactive] = INACTIVE

    # VIEWED -> ENGAGED | INACTIVE
    viewed_mask = grid == VIEWED
    engage_prob = (
        config.P_ENGAGE
        + config.NEIGHBOR_ENGAGE_BOOST * sharing_influence
        + config.HEAT_BOOST_ENGAGE * heat
    )
    engage_prob = clip_grob(
        engage_prob
        * trait_multiplier(activity, config.ENGAGE_ACTIVITY_WEIGHT)
        * trait_multiplier(interest, config.ENGAGE_INTEREST_WEIGHT)
    )
    drop_view_prob = (
        config.P_DROP_VIEW
        + config.INTEREST_DROP_WEIGHT * (1.0 - interest)
        + 0.5 * config.ACTIVITY_DROP_WEIGHT * (1.0 - activity)
    )
    drop_view_prob = clip_grob(drop_view_prob / (1.0 + config.HEAT_PROTECT_VIEW * heat))
    viewed_to_engaged, viewed_to_inactive = resolve_stage_transitions(
        viewed_mask,
        engage_prob,
        drop_view_prob,
        rng,
    )
    new_grid[viewed_to_engaged] = ENGAGED
    new_grid[viewed_to_inactive] = INACTIVE

    # ENGAGED -> SHARING | INACTIVE
    engaged_mask = grid == ENGAGED
    share_prob = (
        config.P_SHARE
        + config.NEIGHBOR_SHARE_BOOST * sharing_influence
        + config.HEAT_BOOST_SHARE * heat
    )
    share_prob = clip_grob(
        share_prob
        * trait_multiplier(activity, config.SHARE_ACTIVITY_WEIGHT)
        * trait_multiplier(interest, config.SHARE_INTEREST_WEIGHT)
    )
    drop_engage_prob = (
        config.P_DROP_ENGAGE
        + 0.5 * config.INTEREST_DROP_WEIGHT * (1.0 - interest)
        + config.ACTIVITY_DROP_WEIGHT * (1.0 - activity)
    )
    drop_engage_prob = clip_grob(drop_engage_prob / (1.0 + config.HEAT_PROTECT_ENGAGE * heat))
    engaged_to_sharing, engaged_to_inactive = resolve_stage_transitions(
        engaged_mask,
        share_prob,
        drop_engage_prob,
        rng,
    )
    new_grid[engaged_to_sharing] = SHARING
    new_grid[engaged_to_inactive] = INACTIVE
    new_sharing_time[engaged_to_sharing] = 0

    # SHARING -> INACTIVE
    sharing_mask = grid == SHARING
    new_sharing_time[sharing_mask] += 1
    fatigue_ratio = new_sharing_time / np.maximum(fatigue_threshold, 1)
    fade_prob = clip_grob(config.P_FADE + config.FATIGUE_GROWTH * fatigue_ratio)
    fade_rand = rng.random(grid.shape)
    forced_fade = (new_sharing_time >= config.MAX_SHARING_STEPS) | (new_sharing_time >= fatigue_threshold)
    sharing_to_inactive = sharing_mask & ((fade_rand < fade_prob) | forced_fade)
    new_grid[sharing_to_inactive] = INACTIVE
    new_sharing_time[sharing_to_inactive] = 0

    counts = count_states(new_grid)
    metrics = {
        "new_exposures": int(np.sum(new_exposed)),
        "new_views": int(np.sum(exposed_to_viewed)),
        "new_engagements": int(np.sum(viewed_to_engaged)),
        "new_shares": int(np.sum(engaged_to_sharing)),
        "new_skips": int(np.sum(exposed_to_inactive)),
        "new_drop_view": int(np.sum(viewed_to_inactive)),
        "new_drop_engage": int(np.sum(engaged_to_inactive)),
        "new_inactive_from_sharing": int(np.sum(sharing_to_inactive)),
        "social_exposed": int(np.sum(social_hits)),
        "recommended_exposed": int(np.sum(recommend_hits)),
        "dual_exposed": int(np.sum(social_hits & recommend_hits)),
        "avg_sharing_neighbors": float(np.mean(sharing_neighbors)),
        "avg_sharing_influence": float(np.mean(sharing_influence)),
        "current_social_reach": int(np.sum(new_source_grid == SOURCE_SOCIAL)),
        "current_recommended_reach": int(np.sum(new_source_grid == SOURCE_RECOMMEND)),
        "max_social_depth": int(np.max(new_social_depth)) if np.any(new_social_depth >= 0) else 0,
        "view_conversion_rate": int(np.sum(exposed_to_viewed)) / max(int(np.sum(exposed_mask)), 1),
        "engagement_rate": int(np.sum(viewed_to_engaged)) / max(int(np.sum(viewed_mask)), 1),
        "share_rate": int(np.sum(engaged_to_sharing)) / max(int(np.sum(engaged_mask)), 1),
        "skip_rate": int(np.sum(exposed_to_inactive)) / max(int(np.sum(exposed_mask)), 1),
        "view_drop_rate": int(np.sum(viewed_to_inactive)) / max(int(np.sum(viewed_mask)), 1),
        "engage_drop_rate": int(np.sum(engaged_to_inactive)) / max(int(np.sum(engaged_mask)), 1),
    }
    return new_grid, new_sharing_time, new_social_depth, new_source_grid, metrics, counts


def run_simulation(config):
    rng = np.random.default_rng(config.RANDOM_SEED)
    grid = creat_grid(config.GRID_SIZE, config.INITIAL_SHARERS, rng)
    sharing_time = np.zeros_like(grid, dtype=np.int16)
    social_depth_grid = np.full_like(grid, -1, dtype=np.int16)
    social_depth_grid[grid == SHARING] = 0
    source_grid = np.full_like(grid, SOURCE_NONE, dtype=np.int8)
    source_grid[grid == SHARING] = SOURCE_SOCIAL
    traits = sample_user_traits(config, rng, grid.shape)

    history_grids = [grid.copy()]
    history = {
        "unseen": [],
        "exposed": [],
        "viewed": [],
        "engaged": [],
        "sharing": [],
        "inactive": [],
        "heat": [],
        "new_exposures": [],
        "new_views": [],
        "new_engagements": [],
        "new_shares": [],
        "new_skips": [],
        "new_drop_view": [],
        "new_drop_engage": [],
        "new_inactive_from_sharing": [],
        "social_exposed": [],
        "recommended_exposed": [],
        "dual_exposed": [],
        "avg_sharing_neighbors": [],
        "avg_sharing_influence": [],
        "cumulative_exposures": [],
        "cumulative_views": [],
        "cumulative_engagements": [],
        "cumulative_shares": [],
        "cumulative_inactive": [],
        "current_social_reach": [],
        "current_recommended_reach": [],
        "view_conversion_rate": [],
        "engagement_rate": [],
        "share_rate": [],
        "skip_rate": [],
        "view_drop_rate": [],
        "engage_drop_rate": [],
        "max_social_depth": [],
    }

    heat = float(np.sum(grid == SHARING))
    initial_counts = count_states(grid)
    for key, value in initial_counts.items():
        history[key].append(value)
    history["heat"].append(heat)
    history["new_exposures"].append(0)
    history["new_views"].append(0)
    history["new_engagements"].append(0)
    history["new_shares"].append(0)
    history["new_skips"].append(0)
    history["new_drop_view"].append(0)
    history["new_drop_engage"].append(0)
    history["new_inactive_from_sharing"].append(0)
    history["social_exposed"].append(0)
    history["recommended_exposed"].append(0)
    history["dual_exposed"].append(0)
    history["avg_sharing_neighbors"].append(
        float(np.mean(get_neighbor_count(grid, SHARING, config.NEIGHBORHOOD)))
    )
    history["avg_sharing_influence"].append(
        float(
            np.mean(
                get_neighbor_values(
                    np.where(grid == SHARING, traits["influence"], 0.0),
                    config.NEIGHBORHOOD,
                )
            )
        )
    )
    history["cumulative_exposures"].append(int(np.sum(grid != UNSEEN)))
    history["cumulative_views"].append(0)
    history["cumulative_engagements"].append(0)
    history["cumulative_shares"].append(0)
    history["cumulative_inactive"].append(0)
    history["current_social_reach"].append(int(np.sum(source_grid == SOURCE_SOCIAL)))
    history["current_recommended_reach"].append(0)
    history["view_conversion_rate"].append(0.0)
    history["engagement_rate"].append(0.0)
    history["share_rate"].append(0.0)
    history["skip_rate"].append(0.0)
    history["view_drop_rate"].append(0.0)
    history["engage_drop_rate"].append(0.0)
    history["max_social_depth"].append(0)

    cumulative_views = 0
    cumulative_engagements = 0
    cumulative_shares = 0

    for _ in range(config.STEPS):
        (
            grid,
            sharing_time,
            social_depth_grid,
            source_grid,
            step_metrics,
            counts,
        ) = step(
            grid=grid,
            sharing_time=sharing_time,
            social_depth_grid=social_depth_grid,
            source_grid=source_grid,
            traits=traits,
            heat=heat,
            rng=rng,
            config=config,
        )

        heat = compute_heat(
            prev_heat=heat,
            sharers=counts["sharing"],
            new_shares=step_metrics["new_shares"],
            heat_decay=config.HEAT_DECAY,
            heat_from_sharers=config.HEAT_FROM_SHARES,
            heat_from_new_shares=config.HEAT_FROM_NEW_SHARES,
        )

        cumulative_views += step_metrics["new_views"]
        cumulative_engagements += step_metrics["new_engagements"]
        cumulative_shares += step_metrics["new_shares"]

        history_grids.append(grid.copy())
        for key, value in counts.items():
            history[key].append(value)
        history["heat"].append(heat)
        history["new_exposures"].append(step_metrics["new_exposures"])
        history["new_views"].append(step_metrics["new_views"])
        history["new_engagements"].append(step_metrics["new_engagements"])
        history["new_shares"].append(step_metrics["new_shares"])
        history["new_skips"].append(step_metrics["new_skips"])
        history["new_drop_view"].append(step_metrics["new_drop_view"])
        history["new_drop_engage"].append(step_metrics["new_drop_engage"])
        history["new_inactive_from_sharing"].append(step_metrics["new_inactive_from_sharing"])
        history["social_exposed"].append(step_metrics["social_exposed"])
        history["recommended_exposed"].append(step_metrics["recommended_exposed"])
        history["dual_exposed"].append(step_metrics["dual_exposed"])
        history["avg_sharing_neighbors"].append(step_metrics["avg_sharing_neighbors"])
        history["avg_sharing_influence"].append(step_metrics["avg_sharing_influence"])
        history["cumulative_exposures"].append(int(np.sum(grid != UNSEEN)))
        history["cumulative_views"].append(cumulative_views)
        history["cumulative_engagements"].append(cumulative_engagements)
        history["cumulative_shares"].append(cumulative_shares)
        history["cumulative_inactive"].append(counts["inactive"])
        history["current_social_reach"].append(step_metrics["current_social_reach"])
        history["current_recommended_reach"].append(step_metrics["current_recommended_reach"])
        history["view_conversion_rate"].append(step_metrics["view_conversion_rate"])
        history["engagement_rate"].append(step_metrics["engagement_rate"])
        history["share_rate"].append(step_metrics["share_rate"])
        history["skip_rate"].append(step_metrics["skip_rate"])
        history["view_drop_rate"].append(step_metrics["view_drop_rate"])
        history["engage_drop_rate"].append(step_metrics["engage_drop_rate"])
        history["max_social_depth"].append(step_metrics["max_social_depth"])

    return history, history_grids
