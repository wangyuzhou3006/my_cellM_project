import numpy as np

UNSEEN = 0      
VIEWED = 1      
SHARING = 2     
INACTIVE = 3

#负责创建初始网格
def creat_grid(size: int, initial_sharers: int, rng: np.random.Generator) -> np.ndarray:
    grid = np.zeros((size,size),dtype=np.int8)
    indices = rng.choice(size*size,size = initial_sharers,replace=False)    #从所有个格子里随机选出若干个位置作为初始传播源，不重复选同一个格子
    rows,cols = np.unravel_index(indices,(size,size))   #把前面选的格子编号转化为二维坐标
    grid[rows,cols] = SHARING   #完成传播者初始化
    return grid

def sample_user_traits(config, rng: np.random.Generator, shape: tuple[int, int]) -> dict:
    activity = clip_grob(rng.normal(config.ACTIVITY_MEAN, config.ACTIVITY_STD, size=shape))
    interest = clip_grob(rng.normal(config.INTEREST_MEAN, config.INTEREST_STD, size=shape))
    influence = np.clip(
        rng.normal(config.INFLUENCE_MEAN, config.INFLUENCE_STD, size=shape),
        0.1,
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
    #对网格中的每一个用户统计他周围有多少个指定状态的邻居
    mask = (grid == state).astype(np.int8)                      #将要统计的指定状态转为1，其余转为0
    return get_neighbor_values(mask, mode)

#更新全局热度
def compute_heat(prev_heat: float, sharers: int, new_shares: int, heat_decay: float, heat_from_sharers: float, heat_from_new_shares: float) -> float:
    return (heat_decay * prev_heat + heat_from_sharers * sharers + heat_from_new_shares * new_shares)

#把概率限制在0和1之间
def clip_grob(x):
    return np.clip(x,0.0,1.0)

#单步更新函数
def step(
    grid: np.ndarray,
    sharing_time: np.ndarray,
    traits: dict,
    heat: float,
    rng: np.random.Generator,
    p_expose: float,
    p_recommend: float,
    p_share: float,
    p_fade: float,
    heat_boost_expose: float,
    heat_boost_recommend: float,
    heat_boost_share: float,
    neighbor_share_boost: float,
    fatigue_growth: float,
    max_sharing_steps: int,
    neighborhood: str
):
    new_grid = grid.copy()
    new_sharing_time = sharing_time.copy()
    sharing_neighbors = get_neighbor_count(grid, SHARING, neighborhood)
    sharing_influence = get_neighbor_values(
        np.where(grid == SHARING, traits["influence"], 0.0),
        neighborhood,
    )
    activity = traits["activity"]
    interest = traits["interest"]
    fatigue_threshold = traits["fatigue_threshold"]
    
    #UNSEEN -> VIEWED
    unseen_mask = (grid == UNSEEN)
    social_expose_prob = 1.0 - (1.0 - p_expose) ** sharing_influence
    social_expose_prob = clip_grob(
        social_expose_prob * (0.5 + 0.5 * activity) * (0.35 + 0.65 * interest)
    )
    recommend_expose_prob = clip_grob(
        (p_recommend + heat_boost_recommend * heat) * (0.45 + 0.55 * activity) * (0.35 + 0.65 * interest)
    )
    social_expose_prob = clip_grob(social_expose_prob + heat_boost_expose * heat)
    social_rand = rng.random(grid.shape)
    recommend_rand = rng.random(grid.shape)
    social_hits = unseen_mask & (social_rand < social_expose_prob)
    recommend_hits = unseen_mask & (recommend_rand < recommend_expose_prob)
    unseen_to_viewed = social_hits | recommend_hits
    new_grid[unseen_to_viewed] = VIEWED
    
    #VIEWED -> SHARING
    viewed_mask = (grid == VIEWED)
    share_prob = clip_grob(
        (p_share + neighbor_share_boost * sharing_influence + heat_boost_share * heat)
        * (0.4 + 0.6 * activity)
        * (0.45 + 0.55 * interest)
    )
    share_rand = rng.random(grid.shape)
    viewed_to_sharing = viewed_mask & (share_rand < share_prob)
    new_grid[viewed_to_sharing] = SHARING
    new_sharing_time[viewed_to_sharing] = 0
    
    #SHARING -> INACTIVE
    sharing_mask = (grid == SHARING)
    new_sharing_time[sharing_mask] += 1     #更新传播时间
    fatigue_ratio = new_sharing_time / np.maximum(fatigue_threshold, 1)
    fade_prob = clip_grob(p_fade + fatigue_growth * fatigue_ratio)   #衰退概率 = 基础概率 + 随时间增长的概率
    fade_rand = rng.random(grid.shape)
    forced_fade = (new_sharing_time >= max_sharing_steps) | (new_sharing_time >= fatigue_threshold)
    sharing_to_inactive = sharing_mask & ((fade_rand < fade_prob) | forced_fade)
    new_grid[sharing_to_inactive] = INACTIVE
    new_sharing_time[sharing_to_inactive] = 0
    
    #统计更新后的状态
    counts = count_states(new_grid)
    new_shares = int(np.sum(viewed_to_sharing))
    exposure_stats = {
        "social_exposed": int(np.sum(social_hits)),
        "recommended_exposed": int(np.sum(recommend_hits)),
        "dual_exposed": int(np.sum(social_hits & recommend_hits)),
        "sharing_neighbors": float(np.mean(sharing_neighbors)),
        "sharing_influence": float(np.mean(sharing_influence)),
    }
    return new_grid, new_sharing_time, new_shares, counts, exposure_stats

#统计网格中各状态用户的数量
def count_states(grid: np.ndarray) -> dict:
    return {
        "unseen": int(np.sum(grid == UNSEEN)),
        "viewed": int(np.sum(grid == VIEWED)),
        "sharing": int(np.sum(grid == SHARING)),
        "inactive": int(np.sum(grid == INACTIVE))
    }

#总控函数
def run_simulation(config):
    #初始化随机数(每次用同一个随机种子，结果可以复现)
    rng = np.random.default_rng(config.RANDOM_SEED)
    grid = creat_grid(config.GRID_SIZE,config.INITIAL_SHARERS,rng)
    sharing_time = np.zeros_like(grid,dtype=np.int16)
    traits = sample_user_traits(config, rng, grid.shape)
    
    #保存历史数据
    history_grids = []
    history_grids.append(grid.copy())
    history = {
        "unseen": [],
        "viewed": [],
        "sharing": [],
        "inactive": [],
        "heat": [],
        "new_shares": [],
        "social_exposed": [],
        "recommended_exposed": [],
        "dual_exposed": [],
        "avg_sharing_neighbors": [],
        "avg_sharing_influence": [],
    }
    heat = float(np.sum(grid == SHARING))
    
    #记录初始统计
    initial_counts = count_states(grid)
    for k,v in initial_counts.items():
        history[k].append(v)
    history["heat"].append(heat)
    history["new_shares"].append(initial_counts["sharing"])
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
    
    #迭代模拟
    for _ in range(config.STEPS):
        grid, sharing_time, new_shares, counts, exposure_stats = step(
            grid=grid,
            sharing_time=sharing_time,
            traits=traits,
            heat=heat,
            rng=rng,
            p_expose=config.P_EXPOSE,
            p_recommend=config.P_RECOMMEND,
            p_share=config.P_SHARE,
            p_fade=config.P_FADE,
            heat_boost_expose=config.HEAT_BOOST_EXPOSE,
            heat_boost_recommend=config.HEAT_BOOST_RECOMMEND,
            heat_boost_share=config.HEAT_BOOST_SHARE,
            neighbor_share_boost=config.NEIGHBOR_SHARE_BOOST,
            fatigue_growth=config.FATIGUE_GROWTH,
            max_sharing_steps=config.MAX_SHARING_STEPS,
            neighborhood=config.NEIGHBORHOOD,
        )
        heat = compute_heat(
            prev_heat=heat,
            sharers=counts["sharing"],
            new_shares=new_shares,
            heat_decay = config.HEAT_DECAY,
            heat_from_sharers=config.HEAT_FROM_SHARES,
            heat_from_new_shares=config.HEAT_FROM_NEW_SHARES,
        )
        
        history_grids.append(grid.copy())
        for k,v in counts.items():
            history[k].append(v)
        history["heat"].append(heat)
        history["new_shares"].append(new_shares)
        history["social_exposed"].append(exposure_stats["social_exposed"])
        history["recommended_exposed"].append(exposure_stats["recommended_exposed"])
        history["dual_exposed"].append(exposure_stats["dual_exposed"])
        history["avg_sharing_neighbors"].append(exposure_stats["sharing_neighbors"])
        history["avg_sharing_influence"].append(exposure_stats["sharing_influence"])
    
    return history,history_grids
    
    
    
    
    
    


    
    
