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
    
def get_neighbor_count(grid: np.ndarray, state: int, mode: str = "moore") -> np.ndarray:
    #对网格中的每一个用户统计他周围有多少个指定状态的邻居
    mask = (grid == state).astype(np.int8)                      #将要统计的指定状态转为1，其余转为0
    padded = np.pad(mask,1,mode="constant",constant_values=0)   #给数组四周补一圈0，防止越界
    
    up = padded[:-2, 1:-1]
    down = padded[2:, 1:-1]
    left = padded[1:-1, :-2]
    right = padded[1:-1, 2:]
    
    if mode == "von_neumann":
        return up + down + left + right

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
    heat: float,
    rng: np.random.Generator,
    p_expose: float,
    p_share: float,
    p_fade: float,
    heat_boost_expose: float,
    heat_boost_share: float,
    max_sharing_steps: int,
    neighborhood: str
):
    new_grid = grid.copy()
    new_sharing_time = sharing_time.copy()
    sharing_neighbors = get_neighbor_count(grid, SHARING, neighborhood)
    
    #UNSEEN -> VIEWED
    unseen_mask = (grid == UNSEEN)
    expose_prob = 1.0 - (1.0 - p_expose) ** sharing_neighbors   #计算被邻居影响的概率之和
    expose_prob = clip_grob(expose_prob + heat_boost_expose * heat)     #加上热度的影响
    expose_rand = rng.random(grid.shape)
    unseen_to_viewed = unseen_mask & (expose_rand < expose_prob)    #如果某个未接触的用户的随机数小于它的曝光概率，就认为他刷到了视频
    new_grid[unseen_to_viewed] = VIEWED
    
    #VIEWED -> SHARING
    viewed_mask = (grid == VIEWED)
    share_prob = clip_grob(p_share + 0.03 * sharing_neighbors + heat_boost_share * heat)
    share_rand = rng.random(grid.shape)
    viewed_to_sharing = viewed_mask & (share_rand < share_prob)
    new_grid[viewed_to_sharing] = SHARING
    new_sharing_time[viewed_to_sharing] = 0
    
    #SHARING -> INACTIVE
    sharing_mask = (grid == SHARING)
    new_sharing_time[sharing_mask] += 1     #更新传播时间
    fade_prob = clip_grob(p_fade + 0.02 * (new_sharing_time / max_sharing_steps))   #衰退概率 = 基础概率 + 随时间增长的概率
    fade_rand = rng.random(grid.shape)
    forced_fade = new_sharing_time >= max_sharing_steps
    sharing_to_inactive = sharing_mask & ((fade_rand < fade_prob) | forced_fade)
    new_grid[sharing_to_inactive] = INACTIVE
    new_sharing_time[sharing_to_inactive] = 0
    
    #统计更新后的状态
    counts = count_states(new_grid)
    new_shares = int(np.sum(viewed_to_sharing))
    return new_grid, new_sharing_time, new_shares, counts

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
    
    #保存历史数据
    history_grids = []
    history_grids.append(grid.copy())
    history = {
        "unseen": [],
        "viewed": [],
        "sharing": [],
        "inactive": [],
        "heat": [],
        "new_shares": []
    }
    heat = float(np.sum(grid == SHARING))
    
    #记录初始统计
    initial_counts = count_states(grid)
    for k,v in initial_counts.items():
        history[k].append(v)
    history["heat"].append(heat)
    history["new_shares"].append(initial_counts["sharing"])
    
    #迭代模拟
    for _ in range(config.STEPS):
        grid, sharing_time, new_shares, counts = step(
            grid=grid,
            sharing_time=sharing_time,
            heat=heat,
            rng=rng,
            p_expose=config.P_EXPOSE,
            p_share=config.P_SHARE,
            p_fade=config.P_FADE,
            heat_boost_expose=config.HEAT_BOOST_EXPOSE,
            heat_boost_share=config.HEAT_BOOST_SHARE,
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
    
    return history,history_grids
    
    
    
    
    
    


    
    