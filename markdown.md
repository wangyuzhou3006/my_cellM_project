# 短视频传播模拟项目说明

## 1. 项目简介

本项目使用二维网格上的元胞自动机思想，模拟短视频内容在用户群体中的传播、扩散和衰退过程。

项目当前目标不是还原真实平台的全部机制，而是在较简单的结构下，展示以下传播现象：

- 初始少量传播者如何触发扩散
- 邻居传播与平台推荐如何共同带来曝光
- 用户个体差异如何影响传播结果
- 热度如何随传播过程增长、衰减并反馈到后续曝光

程序运行后会输出：

- 终端中的模拟摘要
- 用户状态、行为转化、累计漏斗、曝光来源和传播深度曲线
- 传播过程动画

---

## 2. 项目结构

项目主要由以下文件组成：

### `main.py`
程序入口。

职责：

- 读取配置
- 调用模拟主流程
- 计算并打印摘要信息
- 调用可视化模块绘图和动画展示

### `config.py`
项目参数配置文件。

职责：

- 定义网格大小、模拟步数、随机种子
- 定义传播概率、热度参数、动画参数
- 定义用户异质性参数
- 定义平台推荐曝光参数

### `model.py`
传播与演化的核心算法文件。

职责：

- 定义用户状态常量
- 初始化传播网格
- 生成用户个体属性
- 计算邻居影响
- 执行多阶段行为状态更新
- 计算热度
- 记录完整历史数据和转化指标

### `visualize.py`
可视化模块。

职责：

- 绘制状态数量变化曲线
- 绘制状态数量、行为漏斗、累计漏斗、曝光来源、阶段转化/流失率和传播深度曲线
- 显示传播过程动画

### `ablation.py`
分组消融实验脚本。

职责：

- 按预设实验组批量运行模拟
- 生成单随机种子结果表，兼容当前快速分析和绘图流程
- 生成多随机种子明细表、汇总表和相对基准组的变化表，便于更稳定地比较不同机制的重要性

### `plot_ablation.py`
消融结果绘图脚本。

职责：

- 读取 `ablation_summary.csv`
- 读取 `ablation_delta_summary.csv`
- 绘制带标准差误差棒的分组消融实验绝对值对比柱状图
- 绘制相对基准组变化的柱状图
- 输出 `ablation_absolute.png` 和 `ablation_delta.png`

### `markdown.md`
项目说明文档，即当前文件。

### `WORKLOG.md`
开发日志文件，用于记录后续改动、验证结果和待处理事项。

### `PLAN.md`
项目演进路线图，记录后续模型升级方向。

### `ablation_results.csv`
分组消融实验的结果汇总表。

### `ablation_delta.csv`
相对基准组的变化表，用于直接比较各机制被关闭或削弱后的影响。

### `ablation_runs.csv`
多随机种子消融实验的逐次运行明细表。每一行对应一个“实验组 × 随机种子”组合。

### `ablation_summary.csv`
多随机种子消融实验的汇总表。当前按实验组聚合，记录核心指标的均值和标准差。

### `ablation_delta_summary.csv`
多随机种子消融实验相对基准组的均值变化表，用于判断某种机制的重要性是否在多次重复下仍然稳定。

### `ablation_absolute.png`
消融实验绝对值对比图，当前包含最终触达人数、热度峰值、传播人数峰值、热度峰值出现步数和热度时间重心步数五个子图，并使用标准差误差棒表示多随机种子下的波动。

### `ablation_delta.png`
消融实验相对变化对比图，基于 `ablation_delta_summary.csv` 绘制，当前包含最终触达人数、热度峰值、传播人数峰值、热度峰值出现步数和热度时间重心步数五个相对子图。

---

## 3. 模型中的用户状态

项目将每个网格单元视为一个用户，每个用户处于以下 6 种状态之一：

- `UNSEEN = 0`：未看过视频
- `EXPOSED = 1`：刷到视频但未停留观看
- `VIEWED = 2`：停留观看但尚未互动
- `ENGAGED = 3`：已经互动，但尚未主动传播
- `SHARING = 4`：正在传播视频
- `INACTIVE = 5`：沉默或失活，不再继续当前内容链路

状态转移方向为：

`UNSEEN -> EXPOSED -> VIEWED -> ENGAGED -> SHARING -> INACTIVE`

这是一个单向传播过程，用户进入 `INACTIVE` 后不会再次回到当前内容的活跃传播状态；`INACTIVE` 可以来自刷到即流失、观看后流失、互动后流失或传播衰退。

---

## 4. 当前传播机制

## 4.1 邻域传播

用户处在二维网格中，传播会受到邻居影响。

支持两种邻域模式：

- `von_neumann`：上下左右 4 邻域
- `moore`：周围 8 邻域

当前配置默认使用：

`NEIGHBORHOOD = "von_neumann"`

---

## 4.2 用户异质性

与最初“所有用户参数完全相同”的模型不同，当前版本为每个用户生成独立属性：

- 活跃度 `activity`
- 兴趣匹配度 `interest`
- 影响力 `influence`
- 疲劳阈值 `fatigue_threshold`

这些属性会影响：

- 用户被曝光的概率
- 用户从观看转为传播的概率
- 用户传播多久后会衰退
- 传播者对周围用户的影响强弱

这使得传播结果不再完全由统一概率控制，而更接近“不同用户行为不同”的情况。

---

## 4.3 双通道曝光

当前版本把“用户看到视频”的来源拆成两条路径：

### 1. 社交传播曝光
来自邻居中的传播者。

影响因素包括：

- 邻居传播者数量或影响力
- 用户活跃度
- 用户兴趣匹配度
- 当前全局热度

### 2. 平台推荐曝光
来自平台算法推荐，而不是邻居直接传播。

影响因素包括：

- 平台基础推荐概率
- 当前全局热度
- 用户活跃度
- 用户兴趣匹配度

最终只要用户满足任意一条曝光路径，就会从 `UNSEEN` 进入 `EXPOSED`。

曝光概率计算如下。

社交曝光概率：

`P_social = clip((1 - (1 - P_EXPOSE) ^ sharing_influence) * activity_factor * interest_factor + HEAT_BOOST_EXPOSE * heat)`

推荐曝光概率：

`P_recommend = clip((P_RECOMMEND + HEAT_BOOST_RECOMMEND * heat) * activity_factor * interest_factor)`

其中：

- `sharing_influence` 表示邻近传播者影响力之和
- `activity_factor = 1 - w + w * activity`
- `interest_factor = 1 - w + w * interest`
- `clip(x)` 表示把数值裁剪到 `[0, 1]`

---

## 4.4 行为漏斗机制

当前版本不再直接从 `VIEWED` 进入 `SHARING`，而是按更细的行为链推进，并为中间阶段加入流失出口：

1. `EXPOSED -> VIEWED`
刷到内容后，用户可能停留观看。

2. `EXPOSED -> INACTIVE`
刷到内容后，用户也可能直接划过并流失。

3. `VIEWED -> ENGAGED`
完成观看后，用户可能发生互动行为。

4. `VIEWED -> INACTIVE`
观看后没有继续互动，转入沉默或失活。

5. `ENGAGED -> SHARING`
已互动用户进一步转化为传播者。

6. `ENGAGED -> INACTIVE`
互动后没有继续分享，转入沉默或失活。

此外，`EXPOSED`、`VIEWED`、`ENGAGED` 三个中间阶段都设置了最短停留步数。在达到最短停留时间之前，用户只能继续停留在当前状态，不能前进到下一阶段，也不能流失到 `INACTIVE`。

各阶段的转化都会受到以下因素组合影响：

- 阶段基础概率
- 周围传播者的影响力
- 当前热度
- 用户活跃度
- 用户兴趣匹配度

这使模型不再只有“看过/传播”两个中间层，而能表达用户从刷到、停留、互动到分享，并在中途流失的完整漏斗。

中间阶段采用“三分机制”：前进、停留、流失。

以 `EXPOSED` 阶段为例：

前进为观看的原始概率：

`P_view_raw = (P_VIEW + NEIGHBOR_VIEW_BOOST * sharing_influence + HEAT_BOOST_VIEW * heat) * activity_factor * interest_factor`

刷到即流失的原始概率：

`P_skip_raw = (P_SKIP + INTEREST_DROP_WEIGHT * (1 - interest) + ACTIVITY_DROP_WEIGHT * (1 - activity)) / (1 + HEAT_PROTECT_VIEW * heat)`

如果 `P_view_raw + P_skip_raw > 1`，则按比例缩放：

`P_view = P_view_raw / (P_view_raw + P_skip_raw)`

`P_skip = P_skip_raw / (P_view_raw + P_skip_raw)`

停留在 `EXPOSED` 的概率为：

`P_stay_exposed = 1 - P_view - P_skip`

`VIEWED` 和 `ENGAGED` 阶段采用同样结构：

- `VIEWED` 阶段：前进为 `ENGAGED`，流失为 `INACTIVE`
- `ENGAGED` 阶段：前进为 `SHARING`，流失为 `INACTIVE`

对应的原始概率公式分别为：

`P_engage_raw = (P_ENGAGE + NEIGHBOR_ENGAGE_BOOST * sharing_influence + HEAT_BOOST_ENGAGE * heat) * activity_factor * interest_factor`

`P_drop_view_raw = (P_DROP_VIEW + INTEREST_DROP_WEIGHT * (1 - interest) + 0.5 * ACTIVITY_DROP_WEIGHT * (1 - activity)) / (1 + HEAT_PROTECT_VIEW * heat)`

`P_share_raw = (P_SHARE + NEIGHBOR_SHARE_BOOST * sharing_influence + HEAT_BOOST_SHARE * heat) * activity_factor * interest_factor`

`P_drop_engage_raw = (P_DROP_ENGAGE + 0.5 * INTEREST_DROP_WEIGHT * (1 - interest) + ACTIVITY_DROP_WEIGHT * (1 - activity)) / (1 + HEAT_PROTECT_ENGAGE * heat)`

这几组概率在每个阶段内部都会进行归一化处理，剩余部分视为用户停留在当前状态。

当前实现还加入了时间门控条件：

- 当 `exposed_time < MIN_EXPOSED_STEPS` 时，`EXPOSED` 用户不能执行 `VIEWED` 或 `INACTIVE` 转移
- 当 `viewed_time < MIN_VIEWED_STEPS` 时，`VIEWED` 用户不能执行 `ENGAGED` 或 `INACTIVE` 转移
- 当 `engaged_time < MIN_ENGAGED_STEPS` 时，`ENGAGED` 用户不能执行 `SHARING` 或 `INACTIVE` 转移

因此，实际转移可以表示为：

`if stage_time >= MIN_STAGE_STEPS: apply transition probabilities`

`else: stay in current stage`

---

## 4.5 衰退机制

处于 `SHARING` 状态的用户不会永久传播，而会随着时间进入 `INACTIVE`。

衰退受以下因素影响：

- 基础衰退概率
- 已持续传播的时间
- 用户个人疲劳阈值
- 最大传播步数限制

因此，不同用户可能传播时间不同，有的人较快失去兴趣，有的人会持续传播更久。

---

## 4.6 热度机制

项目中维护一个全局热度 `heat`，用于表示内容在整个系统中的总体热度。

热度递推公式为：

`当前热度 = 上一时刻热度 * 热度衰减系数 + 当前传播者贡献 + 新增传播者贡献`

更具体地说：

`heat = heat_decay * prev_heat + heat_from_sharers * sharers + heat_from_new_shares * new_shares`

热度会反过来影响：

- 社交曝光概率
- 平台推荐曝光概率
- 已观看用户的分享概率

因此热度既是结果，也是后续传播的驱动因素。

---

## 5. 程序主流程

程序运行逻辑如下：

1. 从 `config.py` 读取所有参数
2. 初始化随机数生成器
3. 创建初始网格，并随机生成初始传播者
4. 为所有用户生成个体属性
5. 初始化传播深度和统计容器
6. 初始化中间阶段计时器
7. 重复执行每一步传播更新
8. 保存每一步的网格和统计结果
9. 输出摘要信息
10. 绘制统计图和传播动画

---

## 6. 输出数据说明

模拟过程中会记录一组历史数据 `history`，主要包括：

- `unseen`：每一步未接触用户数量
- `exposed`：每一步刷到但未停留用户数量
- `viewed`：每一步已观看但未传播用户数量
- `engaged`：每一步已互动但未传播用户数量
- `sharing`：每一步正在传播用户数量
- `inactive`：每一步失活用户数量
- `heat`：每一步全局热度
- `new_exposures`：每一步新增曝光人数
- `new_views`：每一步新增停留观看人数
- `new_engagements`：每一步新增互动人数
- `new_shares`：每一步新增传播者数量
- `new_skips`：每一步刷到即流失的人数
- `new_drop_view`：每一步观看后流失的人数
- `new_drop_engage`：每一步互动后流失的人数
- `new_inactive_from_sharing`：每一步传播衰退后失活的人数
- `social_exposed`：每一步通过社交链路曝光的人数
- `recommended_exposed`：每一步通过推荐链路曝光的人数
- `dual_exposed`：每一步同时满足两条曝光路径的人数
- `avg_sharing_neighbors`：每一步平均邻居传播强度
- `avg_sharing_influence`：每一步平均邻居影响力
- `cumulative_exposures`：累计已触达用户数量
- `cumulative_views`：累计进入观看阶段的人数
- `cumulative_engagements`：累计进入互动阶段的人数
- `cumulative_shares`：累计进入传播阶段的人数
- `cumulative_inactive`：累计进入失活状态的人数
- `current_social_reach`：当前通过社交链首次触达的人数
- `current_recommended_reach`：当前通过推荐链首次触达的人数
- `view_conversion_rate`：曝光用户转为观看的阶段转化率
- `engagement_rate`：观看用户转为互动的阶段转化率
- `share_rate`：互动用户转为传播的阶段转化率
- `skip_rate`：曝光用户直接流失的阶段比例
- `view_drop_rate`：观看用户流失的阶段比例
- `engage_drop_rate`：互动用户流失的阶段比例
- `max_social_depth`：当前已达到的最大社交传播深度

同时会记录 `history_grids`，即每一步完整的网格状态快照，供动画展示使用。

程序摘要中还会输出：

- 热度峰值及其出现步数
- 最终触达人数
- 整体转化率
- 整体流失率
- 推荐触达规模
- 最大传播深度

这些统计项在当前版本的可视化中会分成 6 组展示：

- 用户状态数量变化
- 行为漏斗阶段新增人数
- 累计漏斗
- 社交曝光、推荐曝光、双重曝光和推荐触达
- 阶段转化率与阶段流失率
- 平均邻居传播强度、平均邻居影响力、热度与社交传播深度

如果运行 `ablation.py`，还会额外输出两份实验结果文件：

- `ablation_results.csv`：每个实验组的绝对结果
- `ablation_delta.csv`：相对 `baseline` 的变化量

当前版本的 `ablation.py` 还会额外输出多随机种子结果：

- `ablation_runs.csv`：逐次运行明细
- `ablation_summary.csv`：按实验组聚合后的均值和标准差
- `ablation_delta_summary.csv`：相对基准组的均值变化

如果运行 `plot_ablation.py`，还会额外输出一张图像：

- `ablation_absolute.png`：基于 `ablation_summary.csv` 的分组消融实验绝对值对比柱状图，包含标准差误差棒，并同时展示 `peak_heat_step` 与 `heat_center_step`
- `ablation_delta.png`：基于 `ablation_delta_summary.csv` 的相对变化柱状图，用于直接比较各实验组相对基准组的变化幅度

当前消融实验默认记录以下核心指标：

- `final_reached`
- `exposure_volume`
- `cumulative_views`
- `cumulative_engagements`
- `cumulative_shares`
- `peak_heat`
- `peak_heat_step`
- `heat_center_step`
- `peak_sharing`
- `peak_sharing_step`
- `overall_view_conversion`
- `overall_engagement_conversion`
- `overall_share_conversion`
- `overall_skip_rate`
- `overall_view_drop_rate`
- `overall_engage_drop_rate`
- `recommended_reach`
- `max_social_depth`
- `steps_to_half_reach`
- `steps_to_half_peak_heat`

这些指标分别覆盖传播规模、传播强度、传播节奏、漏斗结构和传播来源结构。

其中，`heat_center_step` 表示热度时间重心，计算公式为：

`heat_center_step = sum(t * heat_t) / sum(heat_t)`

它不是寻找“最大值出现在哪一步”，而是衡量整条热度曲线主要集中在时间轴的什么位置。在低热度、低振幅场景下，这个指标通常比 `peak_heat_step` 更稳定。

在多随机种子模式下，`ablation.py` 默认会对每个实验组使用 5 个随机种子重复运行，并对以下核心指标计算均值和标准差：

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

这样可以减少单次随机样本对结论的影响，让机制重要性分析更稳定。

---

## 7. 如何运行

建议在安装了 `numpy` 和 `matplotlib` 的 Python 环境中运行。

直接运行方式：

```bash
python my_cellM_project/main.py
```

运行分组消融实验：

```bash
python my_cellM_project/ablation.py
```

运行完成后会在项目根目录生成：

- `ablation_results.csv`
- `ablation_delta.csv`
- `ablation_runs.csv`
- `ablation_summary.csv`
- `ablation_delta_summary.csv`

绘制绝对值对比柱状图：

```bash
python my_cellM_project/plot_ablation.py
```

运行完成后会在项目根目录生成：

- `ablation_absolute.png`
- `ablation_delta.png`

如果使用 conda 环境，应确保运行命令对应的解释器中已经安装：

- `numpy`
- `matplotlib`

如果只想测试程序是否能执行，而不弹出图形窗口，可以在非交互后端下运行：

```bash
MPLBACKEND=Agg python my_cellM_project/main.py
```

---

## 8. 当前配置项概览

`config.py` 中主要参数可分为几类：

### 基础规模参数

- `GRID_SIZE`
- `STEPS`
- `RANDOM_SEED`
- `INITIAL_SHARERS`

其中，`INITIAL_SHARERS` 会直接影响传播前期节奏：初始传播源越少，传播越倾向于从局部缓慢展开，而不是在早期快速铺开。

### 传播基础参数

- `P_EXPOSE`
- `P_VIEW`
- `P_ENGAGE`
- `P_SHARE`
- `P_FADE`
- `P_SKIP`
- `P_DROP_VIEW`
- `P_DROP_ENGAGE`

### 个体异质性参数

- `ACTIVITY_MEAN`
- `ACTIVITY_STD`
- `INTEREST_MEAN`
- `INTEREST_STD`
- `INFLUENCE_MEAN`
- `INFLUENCE_STD`
- `INFLUENCE_MIN`
- `FATIGUE_THRESHOLD_MIN`
- `FATIGUE_THRESHOLD_MAX`

### 热度反馈参数

- `HEAT_BOOST_EXPOSE`
- `HEAT_BOOST_RECOMMEND`
- `HEAT_BOOST_VIEW`
- `HEAT_BOOST_ENGAGE`
- `HEAT_BOOST_SHARE`
- `HEAT_PROTECT_VIEW`
- `HEAT_PROTECT_ENGAGE`
- `HEAT_DECAY`
- `HEAT_FROM_SHARES`
- `HEAT_FROM_NEW_SHARES`

### 阶段权重与局部影响参数

- `P_RECOMMEND`
- `EXPOSE_ACTIVITY_WEIGHT`
- `EXPOSE_INTEREST_WEIGHT`
- `RECOMMEND_ACTIVITY_WEIGHT`
- `RECOMMEND_INTEREST_WEIGHT`
- `VIEW_ACTIVITY_WEIGHT`
- `VIEW_INTEREST_WEIGHT`
- `ENGAGE_ACTIVITY_WEIGHT`
- `ENGAGE_INTEREST_WEIGHT`
- `SHARE_ACTIVITY_WEIGHT`
- `SHARE_INTEREST_WEIGHT`
- `NEIGHBOR_VIEW_BOOST`
- `NEIGHBOR_ENGAGE_BOOST`
- `NEIGHBOR_SHARE_BOOST`
- `FATIGUE_GROWTH`
- `INTEREST_DROP_WEIGHT`
- `ACTIVITY_DROP_WEIGHT`

### 运行与显示参数

- `MAX_SHARING_STEPS`
- `MIN_EXPOSED_STEPS`
- `MIN_VIEWED_STEPS`
- `MIN_ENGAGED_STEPS`
- `INTERVAL`
- `NEIGHBORHOOD`

`MIN_EXPOSED_STEPS`、`MIN_VIEWED_STEPS`、`MIN_ENGAGED_STEPS` 是当前版本中控制传播节奏的重要参数。它们越大，中间状态停留时间越长，峰值通常越晚出现，整个传播过程也越不容易过早趋稳。与此同时，`P_EXPOSE` 越低，社交链的扩散起点越弱，传播会更偏向缓慢展开而不是快速铺开。

---

## 9. 项目特点

当前项目有以下特点：

- 结构简单，便于阅读和教学演示
- 使用 NumPy 做网格计算，逻辑清晰
- 已从同质用户模型升级到异质用户模型
- 已支持“社交传播 + 平台推荐”的双通道曝光
- 已支持更细的行为漏斗和更完整的统计输出
- 已支持按机制分组的消融实验分析
- 已支持带标准差误差棒的消融结果绝对值柱状图输出
- 已支持相对基准组变化的消融结果柱状图输出
- 可同时输出统计曲线和传播动画

---

## 10. 当前局限

虽然当前版本比最初更拟真，但仍然有明显简化：

- 用户关系仍然是规则网格，不是真实社交网络
- 互动状态仍是单一层，尚未区分点赞、评论、收藏等行为
- 平台推荐仍用简化概率表示，没有完整推荐策略
- 用户进入 `INACTIVE` 后不会再被重新激活
- 社交传播深度仍然偏浅，后续仍可能需要从传播拓扑或深度定义上继续改进
- 目前没有自动化测试文件和正式依赖清单

因此，该项目更适合作为传播模拟实验和算法演示，而不是直接作为真实平台行为预测工具。

---

## 11. 后续可扩展方向

结合当前 `PLAN.md`，后续可以继续向以下方向升级：

- 引入更细的用户行为状态
- 用图网络替代二维网格
- 引入社区结构和强弱连接
- 引入阈值模型或 Hawkes 过程
- 增加实验结果导出能力
- 增加测试和参数校验

---

## 12. 总结

本项目是一个短视频传播模拟器，核心思路是在二维用户网格上，用状态转移、热度反馈、用户异质性和双通道曝光机制，模拟内容从少量传播者开始逐步扩散、达到峰值并最终衰退的过程。

它已经具备完整的最小闭环：

- 可配置
- 可运行
- 可统计
- 可视化
- 可继续演进

如果后续继续完善用户行为、传播网络和平台推荐策略，这个项目可以进一步发展成更拟真的传播模拟实验平台。
