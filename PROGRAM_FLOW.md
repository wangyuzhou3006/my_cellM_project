# 程序流程说明

## 1. 程序做什么

这个程序用二维网格模拟短视频在用户群体中的传播过程。

每个网格单元代表一个用户。用户会在不同状态之间转移，并受到以下因素影响：

- 邻居中传播者的影响
- 平台推荐
- 用户个体差异
- 内容全局热度
- 中间阶段的停留时间和流失机制

程序运行后会：

1. 执行传播模拟
2. 输出摘要信息
3. 绘制统计图
4. 播放传播动画

---

## 2. 文件分工

### `config.py`
存放所有参数。

### `model.py`
实现核心传播算法。

### `main.py`
程序入口，负责运行模拟、打印摘要、调用可视化。

### `visualize.py`
负责曲线图和动画展示。

---

## 3. 用户状态

程序中每个用户有 6 种状态：

- `UNSEEN`：未触达
- `EXPOSED`：刷到但未停留
- `VIEWED`：停留观看
- `ENGAGED`：已经互动但未分享
- `SHARING`：正在传播
- `INACTIVE`：沉默或失活

主状态链为：

`UNSEEN -> EXPOSED -> VIEWED -> ENGAGED -> SHARING -> INACTIVE`

其中中间状态也可以直接流失到 `INACTIVE`。

---

## 4. 程序主流程

### 第一步：读取配置

`main.py` 从 `config.py` 读取网格大小、传播概率、热度参数、停留步数等配置。

### 第二步：初始化系统

`run_simulation()` 会初始化：

- 随机数生成器
- 初始传播网格
- 传播者持续时间 `sharing_time`
- 中间状态停留计时器
  - `exposed_time`
  - `viewed_time`
  - `engaged_time`
- 社交传播深度 `social_depth_grid`
- 首次触达来源 `source_grid`
- 用户个体属性
  - `activity`
  - `interest`
  - `influence`
  - `fatigue_threshold`

### 第三步：逐步更新状态

每一步都调用 `step()`，按固定顺序更新：

1. `UNSEEN -> EXPOSED`
2. `EXPOSED -> VIEWED / INACTIVE / 留在原状态`
3. `VIEWED -> ENGAGED / INACTIVE / 留在原状态`
4. `ENGAGED -> SHARING / INACTIVE / 留在原状态`
5. `SHARING -> INACTIVE / 留在原状态`
6. 更新热度
7. 记录统计结果

### 第四步：输出结果

模拟结束后：

- `main.py` 打印摘要
- `visualize.py` 绘制统计图
- `visualize.py` 播放网格动画

---

## 5. 核心公式

## 5.1 社交曝光概率

未触达用户可能因为邻居传播者而刷到内容。

公式：

`P_social = clip((1 - (1 - P_EXPOSE) ^ sharing_influence) * activity_factor * interest_factor + HEAT_BOOST_EXPOSE * heat)`

解释：

- `sharing_influence`：邻居传播者影响力总和
- `P_EXPOSE`：基础社交曝光概率
- `activity_factor`：活跃度修正
- `interest_factor`：兴趣匹配修正
- `heat`：当前全局热度
- `clip(x)`：把概率限制在 `[0, 1]`

含义：
邻居传播越强、用户越活跃、兴趣越匹配、热度越高，社交曝光概率越大。

## 5.2 推荐曝光概率

未触达用户也可能因为平台推荐而刷到内容。

公式：

`P_recommend = clip((P_RECOMMEND + HEAT_BOOST_RECOMMEND * heat) * activity_factor * interest_factor)`

解释：

- `P_RECOMMEND`：基础推荐曝光概率
- `HEAT_BOOST_RECOMMEND * heat`：热度带来的推荐增强

含义：
平台推荐会随着热度上升而增强，但仍会受到用户活跃度和兴趣匹配影响。

## 5.3 中间阶段前进概率

以 `EXPOSED -> VIEWED` 为例：

`P_view_raw = (P_VIEW + NEIGHBOR_VIEW_BOOST * sharing_influence + HEAT_BOOST_VIEW * heat) * activity_factor * interest_factor`

类似地：

- `VIEWED -> ENGAGED`

`P_engage_raw = (P_ENGAGE + NEIGHBOR_ENGAGE_BOOST * sharing_influence + HEAT_BOOST_ENGAGE * heat) * activity_factor * interest_factor`

- `ENGAGED -> SHARING`

`P_share_raw = (P_SHARE + NEIGHBOR_SHARE_BOOST * sharing_influence + HEAT_BOOST_SHARE * heat) * activity_factor * interest_factor`

含义：
用户越活跃、兴趣越匹配、周围传播越强、热度越高，就越容易进入下一阶段。

## 5.4 中间阶段流失概率

以 `EXPOSED -> INACTIVE` 为例：

`P_skip_raw = (P_SKIP + INTEREST_DROP_WEIGHT * (1 - interest) + ACTIVITY_DROP_WEIGHT * (1 - activity)) / (1 + HEAT_PROTECT_VIEW * heat)`

类似地：

- `VIEWED -> INACTIVE`

`P_drop_view_raw = (P_DROP_VIEW + INTEREST_DROP_WEIGHT * (1 - interest) + 0.5 * ACTIVITY_DROP_WEIGHT * (1 - activity)) / (1 + HEAT_PROTECT_VIEW * heat)`

- `ENGAGED -> INACTIVE`

`P_drop_engage_raw = (P_DROP_ENGAGE + 0.5 * INTEREST_DROP_WEIGHT * (1 - interest) + ACTIVITY_DROP_WEIGHT * (1 - activity)) / (1 + HEAT_PROTECT_ENGAGE * heat)`

含义：
兴趣越低、活跃度越低，越容易中途流失；热度越高，越能减少中途流失。

## 5.5 三分机制

每个中间阶段都不是“只前进”，而是三选一：

- 前进
- 流失
- 停留

如果前进概率和流失概率之和大于 1，程序会先做归一化：

`P_forward = P_forward_raw / (P_forward_raw + P_drop_raw)`

`P_drop = P_drop_raw / (P_forward_raw + P_drop_raw)`

停留概率：

`P_stay = 1 - P_forward - P_drop`

含义：
这样可以避免概率总和超过 1。

## 5.6 最短停留步数门控

对 `EXPOSED`、`VIEWED`、`ENGAGED`，程序增加了最短停留步数限制：

- `MIN_EXPOSED_STEPS`
- `MIN_VIEWED_STEPS`
- `MIN_ENGAGED_STEPS`

规则：

`if stage_time < MIN_STAGE_STEPS: stay`

`if stage_time >= MIN_STAGE_STEPS: apply transition probabilities`

含义：
用户在达到最短停留时间之前，不能前进，也不能流失，只能停留。

## 5.7 传播者衰退概率

传播者不会永久传播，会随时间失活。

公式：

`fatigue_ratio = sharing_time / fatigue_threshold`

`P_fade = clip(P_FADE + FATIGUE_GROWTH * fatigue_ratio)`

如果：

- `sharing_time >= MAX_SHARING_STEPS`
  或
- `sharing_time >= fatigue_threshold`

则强制失活。

含义：
传播时间越长，失活概率越高。

## 5.8 热度更新公式

热度在每一步更新：

`heat = HEAT_DECAY * prev_heat + HEAT_FROM_SHARES * sharers + HEAT_FROM_NEW_SHARES * new_shares`

解释：

- `prev_heat`：上一时刻热度
- `HEAT_DECAY`：热度保留率
- `sharers`：当前传播者人数
- `new_shares`：新增传播者人数

含义：
热度会衰减，但当前传播者和新增传播者会把热度继续抬高。

---

## 6. 关键变量说明

### 网格与状态变量

- `grid`：当前用户状态网格
- `history_grids`：每一步的网格快照

### 时间变量

- `sharing_time`：传播者已经传播了多久
- `exposed_time`：用户在 `EXPOSED` 停留多久
- `viewed_time`：用户在 `VIEWED` 停留多久
- `engaged_time`：用户在 `ENGAGED` 停留多久

### 个体属性变量

- `activity`：用户活跃度
- `interest`：用户与内容的兴趣匹配度
- `influence`：用户传播影响力
- `fatigue_threshold`：用户疲劳阈值

### 传播结构变量

- `sharing_neighbors`：邻居中传播者数量
- `sharing_influence`：邻居传播影响力总和
- `social_depth_grid`：用户首次通过社交链触达时的深度
- `source_grid`：用户首次触达来源

### 统计变量

- `history`：保存每一步统计结果
- `heat`：全局热度

---

## 7. 关键算法实现

## 7.1 邻居统计

程序用数组平移的方式统计上下左右或八邻域，不使用逐个格子循环。

核心函数：

- `get_neighbor_values()`
- `get_neighbor_count()`
- `get_neighbor_max()`

作用：

- 计算邻居传播者数量
- 计算邻居传播影响力总和
- 计算邻居中最大的社交传播深度

## 7.2 状态更新顺序

每一步都按固定顺序更新，这是为了避免同一步内“新状态立即再次传播”造成混乱。

程序使用旧网格 `grid` 计算转移条件，把结果写入新网格 `new_grid`，属于同步更新。

## 7.3 首次触达来源记录

程序区分用户是首次通过：

- 社交传播触达
- 推荐系统触达

如果两者同时发生，优先记为社交触达，并同时记录双重曝光统计。

## 7.4 历史统计记录

每一步结束后，程序会把状态人数、阶段新增、累计漏斗、阶段转化率、流失率、热度、传播深度等信息全部写入 `history`，供摘要输出和可视化使用。

---

## 8. 参数说明

### 规模参数

- `GRID_SIZE`：网格边长
- `STEPS`：总模拟步数
- `RANDOM_SEED`：随机种子
- `INITIAL_SHARERS`：初始传播者数量

### 基础阶段概率

- `P_EXPOSE`：社交曝光基础概率
- `P_VIEW`：观看基础概率
- `P_ENGAGE`：互动基础概率
- `P_SHARE`：分享基础概率
- `P_FADE`：传播衰退基础概率
- `P_SKIP`：刷到即流失基础概率
- `P_DROP_VIEW`：观看后流失基础概率
- `P_DROP_ENGAGE`：互动后流失基础概率

### 推荐参数

- `P_RECOMMEND`：基础推荐曝光概率
- `HEAT_BOOST_RECOMMEND`：热度对推荐的增强

### 热度参数

- `HEAT_BOOST_EXPOSE`
- `HEAT_BOOST_VIEW`
- `HEAT_BOOST_ENGAGE`
- `HEAT_BOOST_SHARE`
- `HEAT_PROTECT_VIEW`
- `HEAT_PROTECT_ENGAGE`
- `HEAT_DECAY`
- `HEAT_FROM_SHARES`
- `HEAT_FROM_NEW_SHARES`

### 邻居影响参数

- `NEIGHBOR_VIEW_BOOST`
- `NEIGHBOR_ENGAGE_BOOST`
- `NEIGHBOR_SHARE_BOOST`

### 个体属性参数

- `ACTIVITY_MEAN`, `ACTIVITY_STD`
- `INTEREST_MEAN`, `INTEREST_STD`
- `INFLUENCE_MEAN`, `INFLUENCE_STD`, `INFLUENCE_MIN`
- `FATIGUE_THRESHOLD_MIN`, `FATIGUE_THRESHOLD_MAX`

### 节奏控制参数

- `MAX_SHARING_STEPS`
- `MIN_EXPOSED_STEPS`
- `MIN_VIEWED_STEPS`
- `MIN_ENGAGED_STEPS`

这些参数越大，中间状态停留越久，传播节奏越慢。

---

## 9. 当前实现特点

当前程序的特点是：

- 结构清晰，便于阅读
- 使用向量化数组计算，效率较高
- 既考虑社交传播，也考虑平台推荐
- 有中间阶段停留和流失机制
- 可直接输出统计结果和动画

它适合做传播机制演示、参数实验和模型迭代基础。
