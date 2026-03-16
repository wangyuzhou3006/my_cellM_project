# 程序流程说明

## 1. 项目现在包含什么

当前项目已经不只是“单次传播模拟”。它包含三条相互衔接的流程：

1. 主模拟流程  
   从 [`main.py`](/Users/zhou/project/my_cellM_project/main.py) 启动，运行一次传播模拟，打印摘要，并调用 [`visualize.py`](/Users/zhou/project/my_cellM_project/visualize.py) 输出统计图和动画。

2. 分组消融实验流程  
   从 [`ablation.py`](/Users/zhou/project/my_cellM_project/ablation.py) 启动，按预设实验组和多个随机种子重复运行模拟，生成对比用的 CSV 结果表。

3. 消融结果绘图流程  
   从 [`plot_ablation.py`](/Users/zhou/project/my_cellM_project/plot_ablation.py) 启动，读取消融实验的汇总结果，输出绝对值图和相对变化图。

因此，项目当前的完整结构可以理解为：

`配置 -> 模拟 -> 统计 -> 可视化 -> 消融实验 -> 结果汇总 -> 结果绘图`

---

## 2. 文件分工

### 主模拟相关

- [`config.py`](/Users/zhou/project/my_cellM_project/config.py)  
  存放网格大小、步数、随机种子、传播概率、热度参数、个体异质性参数、阶段最短停留步数等全部配置。

- [`model.py`](/Users/zhou/project/my_cellM_project/model.py)  
  实现传播与演化算法，包括状态更新、热度更新、用户异质性、统计记录等。

- [`main.py`](/Users/zhou/project/my_cellM_project/main.py)  
  单次模拟入口，负责调用 `run_simulation()`，打印摘要，并调用可视化。

- [`visualize.py`](/Users/zhou/project/my_cellM_project/visualize.py)  
  输出单次模拟的统计图和网格动画。

### 消融实验相关

- [`ablation.py`](/Users/zhou/project/my_cellM_project/ablation.py)  
  分组消融实验入口，负责批量运行实验、输出单次结果、多随机种子明细、汇总表和相对基准组变化表。

- [`plot_ablation.py`](/Users/zhou/project/my_cellM_project/plot_ablation.py)  
  读取消融实验结果，输出绝对值柱状图和相对变化柱状图。

### 文档与结果

- [`markdown.md`](/Users/zhou/project/my_cellM_project/markdown.md)  
  项目总说明。

- [`WORKLOG.md`](/Users/zhou/project/my_cellM_project/WORKLOG.md)  
  开发日志。

- [`PLAN.md`](/Users/zhou/project/my_cellM_project/PLAN.md)  
  后续演进路线。

- [`ablation_results.csv`](/Users/zhou/project/my_cellM_project/ablation_results.csv)  
  单随机种子实验结果。

- [`ablation_delta.csv`](/Users/zhou/project/my_cellM_project/ablation_delta.csv)  
  单随机种子相对基准组变化。

- [`ablation_runs.csv`](/Users/zhou/project/my_cellM_project/ablation_runs.csv)  
  多随机种子逐次运行明细。

- [`ablation_summary.csv`](/Users/zhou/project/my_cellM_project/ablation_summary.csv)  
  多随机种子按实验组聚合后的均值和标准差。

- [`ablation_delta_summary.csv`](/Users/zhou/project/my_cellM_project/ablation_delta_summary.csv)  
  多随机种子相对基准组的均值变化。

- [`ablation_absolute.png`](/Users/zhou/project/my_cellM_project/ablation_absolute.png)  
  消融实验绝对值对比图。

- [`ablation_delta.png`](/Users/zhou/project/my_cellM_project/ablation_delta.png)  
  消融实验相对变化对比图。

---

## 3. 主模拟流程

### 3.1 启动入口

运行：

```bash
python my_cellM_project/main.py
```

[`main.py`](/Users/zhou/project/my_cellM_project/main.py) 会执行：

1. 调用 [`model.py`](/Users/zhou/project/my_cellM_project/model.py) 中的 `run_simulation(config)`
2. 从返回的 `history` 中提取摘要指标
3. 在终端打印摘要
4. 调用 [`visualize.py`](/Users/zhou/project/my_cellM_project/visualize.py) 输出统计图和动画

### 3.2 初始化

`run_simulation(config)` 的初始化步骤如下：

1. 用 `config.RANDOM_SEED` 初始化随机数生成器  
2. 创建初始网格 `grid`
3. 生成初始传播者
4. 初始化传播者持续时间 `sharing_time`
5. 初始化中间阶段计时器
   - `exposed_time`
   - `viewed_time`
   - `engaged_time`
6. 初始化社交传播深度 `social_depth_grid`
7. 初始化首次触达来源 `source_grid`
8. 为每个用户采样个体属性
   - `activity`
   - `interest`
   - `influence`
   - `fatigue_threshold`
9. 初始化 `history` 和 `history_grids`

### 3.3 单步更新顺序

每一步由 [`model.py`](/Users/zhou/project/my_cellM_project/model.py) 中的 `step()` 完成，顺序固定：

1. `UNSEEN -> EXPOSED`
2. `EXPOSED -> VIEWED / INACTIVE / 留在原状态`
3. `VIEWED -> ENGAGED / INACTIVE / 留在原状态`
4. `ENGAGED -> SHARING / INACTIVE / 留在原状态`
5. `SHARING -> INACTIVE / 留在原状态`
6. 用当前传播结果更新热度
7. 记录本步状态统计和累计指标

### 3.4 输出结果

单次模拟结束后，程序会输出：

- 终端摘要  
  例如热度峰值、最终触达人数、推荐触达规模、整体转化率等

- 统计图  
  包括状态数量、漏斗新增、累计漏斗、曝光来源、阶段转化率、传播深度等

- 网格动画  
  逐步展示整个传播过程

---

## 4. 状态与传播机制

### 4.1 用户状态

当前状态一共 6 个：

- `UNSEEN`：未触达
- `EXPOSED`：刷到但未停留
- `VIEWED`：停留观看
- `ENGAGED`：已互动但未分享
- `SHARING`：正在传播
- `INACTIVE`：沉默或失活

主状态链是：

`UNSEEN -> EXPOSED -> VIEWED -> ENGAGED -> SHARING -> INACTIVE`

其中 `EXPOSED`、`VIEWED`、`ENGAGED` 都允许中途流失到 `INACTIVE`。

### 4.2 双通道曝光

`UNSEEN` 用户进入 `EXPOSED` 有两条路径：

1. 社交曝光
2. 平台推荐曝光

社交曝光概率：

`P_social = clip((1 - (1 - P_EXPOSE) ^ sharing_influence) * activity_factor * interest_factor + HEAT_BOOST_EXPOSE * heat)`

推荐曝光概率：

`P_recommend = clip((P_RECOMMEND + HEAT_BOOST_RECOMMEND * heat) * activity_factor * interest_factor)`

其中：

- `sharing_influence`：邻居传播者影响力之和
- `activity_factor = 1 - w + w * activity`
- `interest_factor = 1 - w + w * interest`
- `clip(x)`：将值截断到 `[0, 1]`

### 4.3 中间阶段三分机制

`EXPOSED`、`VIEWED`、`ENGAGED` 都采用“前进 / 流失 / 停留”的三分机制。

以 `EXPOSED` 阶段为例：

前进概率原型：

`P_view_raw = (P_VIEW + NEIGHBOR_VIEW_BOOST * sharing_influence + HEAT_BOOST_VIEW * heat) * activity_factor * interest_factor`

流失概率原型：

`P_skip_raw = (P_SKIP + INTEREST_DROP_WEIGHT * (1 - interest) + ACTIVITY_DROP_WEIGHT * (1 - activity)) / (1 + HEAT_PROTECT_VIEW * heat)`

如果前进和流失之和大于 1，则做归一化：

`P_forward = P_forward_raw / (P_forward_raw + P_drop_raw)`

`P_drop = P_drop_raw / (P_forward_raw + P_drop_raw)`

停留概率为：

`P_stay = 1 - P_forward - P_drop`

`VIEWED -> ENGAGED / INACTIVE` 和 `ENGAGED -> SHARING / INACTIVE` 使用同样结构，只是对应的基础概率和局部加成参数不同。

### 4.4 最短停留步数门控

为了避免传播过快趋稳，中间阶段增加了最短停留步数限制：

- `MIN_EXPOSED_STEPS`
- `MIN_VIEWED_STEPS`
- `MIN_ENGAGED_STEPS`

规则是：

`if stage_time < MIN_STAGE_STEPS: stay`

也就是说，在达到最短停留时间之前，用户不能前进，也不能流失。

### 4.5 传播者衰退

传播者不会一直传播。其失活概率由基础失活率和疲劳共同决定：

`fatigue_ratio = sharing_time / fatigue_threshold`

`P_fade = clip(P_FADE + FATIGUE_GROWTH * fatigue_ratio)`

同时，如果：

- `sharing_time >= MAX_SHARING_STEPS`
  或
- `sharing_time >= fatigue_threshold`

则强制失活。

### 4.6 热度更新

每一步结束后更新热度：

`heat = HEAT_DECAY * prev_heat + HEAT_FROM_SHARES * sharers + HEAT_FROM_NEW_SHARES * new_shares`

这个热度既是传播结果，也是下一步曝光和转化的重要输入。

---

## 5. 主模拟里的关键统计

`run_simulation()` 当前会把结果写入 `history`。主要包括 5 类：

### 5.1 状态数量

- `unseen`
- `exposed`
- `viewed`
- `engaged`
- `sharing`
- `inactive`

### 5.2 每步新增

- `new_exposures`
- `new_views`
- `new_engagements`
- `new_shares`
- `new_skips`
- `new_drop_view`
- `new_drop_engage`
- `new_inactive_from_sharing`

### 5.3 曝光来源与局部传播

- `social_exposed`
- `recommended_exposed`
- `dual_exposed`
- `avg_sharing_neighbors`
- `avg_sharing_influence`
- `current_social_reach`
- `current_recommended_reach`
- `max_social_depth`

### 5.4 累计漏斗

- `cumulative_exposures`
- `cumulative_views`
- `cumulative_engagements`
- `cumulative_shares`
- `cumulative_inactive`

### 5.5 阶段转化率

- `view_conversion_rate`
- `engagement_rate`
- `share_rate`
- `skip_rate`
- `view_drop_rate`
- `engage_drop_rate`

此外，`history_grids` 会保存每一步完整网格，专门用于动画。

---

## 6. 消融实验流程

### 6.1 启动入口

运行：

```bash
python my_cellM_project/ablation.py
```

[`ablation.py`](/Users/zhou/project/my_cellM_project/ablation.py) 会执行两层实验：

1. 单随机种子版本  
   用当前 `config.RANDOM_SEED` 生成：
   - `ablation_results.csv`
   - `ablation_delta.csv`

2. 多随机种子版本  
   当前默认用 5 个随机种子，生成：
   - `ablation_runs.csv`
   - `ablation_summary.csv`
   - `ablation_delta_summary.csv`

### 6.2 实验组

当前预设 8 组：

- `baseline`
- `no_recommend`
- `weak_social`
- `no_heat_feedback`
- `no_heterogeneity`
- `no_dropout`
- `no_stage_gating`
- `slow_seed`

每组都只改一部分配置，其他参数保持基准不变。

### 6.3 多随机种子运行

多随机种子流程是：

1. 外层遍历实验组
2. 内层遍历随机种子列表 `SEEDS`
3. 对每个“实验组 × 随机种子”调用一次 `run_simulation()`
4. 把单次结果写入 `ablation_runs.csv`
5. 按实验组聚合均值和标准差，写入 `ablation_summary.csv`
6. 再相对 `baseline` 计算均值变化，写入 `ablation_delta_summary.csv`

### 6.4 消融实验里的核心指标

当前多随机种子汇总主要关注：

- `final_reached`
- `peak_heat`
- `peak_heat_step`
- `heat_center_step`
- `peak_sharing`
- `overall_view_conversion`
- `overall_engagement_conversion`
- `overall_share_conversion`
- `recommended_reach`
- `max_social_depth`

其中 `heat_center_step` 是新增的稳健节奏指标：

`heat_center_step = sum(t * heat_t) / sum(heat_t)`

它表示热度在时间轴上的“重心位置”，比单纯看 `peak_heat_step` 更适合低热度、低振幅场景。

---

## 7. 消融结果绘图流程

### 7.1 启动入口

运行：

```bash
python my_cellM_project/plot_ablation.py
```

### 7.2 绝对值图

脚本读取：

- [`ablation_summary.csv`](/Users/zhou/project/my_cellM_project/ablation_summary.csv)

输出：

- [`ablation_absolute.png`](/Users/zhou/project/my_cellM_project/ablation_absolute.png)

当前包含 5 个子图：

- 最终触达人数
- 热度峰值
- 传播人数峰值
- 热度峰值出现步数
- 热度时间重心步数

这些子图显示的是多随机种子均值，并带标准差误差棒。

### 7.3 相对变化图

脚本读取：

- [`ablation_delta_summary.csv`](/Users/zhou/project/my_cellM_project/ablation_delta_summary.csv)

输出：

- [`ablation_delta.png`](/Users/zhou/project/my_cellM_project/ablation_delta.png)

当前包含 5 个相对子图：

- 最终触达人数相对变化
- 热度峰值相对变化
- 传播人数峰值相对变化
- 热度峰值出现步数变化
- 热度时间重心步数变化

其中：

- 规模和强度指标用百分比表示
- 时间指标用步数差表示
- 颜色区分相对上升和相对下降

---

## 8. 当前最重要的流程关系

如果只抓主线，当前项目可以简化成下面这张流程图：

### 单次模拟主线

`config.py -> main.py -> model.run_simulation() -> history/history_grids -> visualize.py`

### 消融实验主线

`config.py + ablation.py -> 多组配置覆盖 -> 多随机种子运行 -> ablation_runs.csv / ablation_summary.csv / ablation_delta_summary.csv`

### 消融绘图主线

`ablation_summary.csv -> plot_ablation.py -> ablation_absolute.png`

`ablation_delta_summary.csv -> plot_ablation.py -> ablation_delta.png`

---

## 9. 如何使用这份文档

如果你要理解项目：

1. 先看“第 3 节主模拟流程”
2. 再看“第 4 节状态与传播机制”
3. 然后看“第 6 节消融实验流程”
4. 最后看“第 7 节消融结果绘图流程”

如果你要改代码：

- 改传播机制，优先看 [`model.py`](/Users/zhou/project/my_cellM_project/model.py)
- 改实验分组，优先看 [`ablation.py`](/Users/zhou/project/my_cellM_project/ablation.py)
- 改结果图，优先看 [`plot_ablation.py`](/Users/zhou/project/my_cellM_project/plot_ablation.py)

这份文档的目标不是重复所有参数说明，而是让你快速知道：

- 程序从哪里开始跑
- 每一步做了什么
- 数据最后流向哪里
- 当前新增的实验和图像功能如何接入整个项目
