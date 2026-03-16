# Work Log

用于记录项目后续的实际改动、问题定位、验证结果和待办事项。
`PLAN.md` 负责规划，本文档负责过程日志。

## 2026-03-16
- Topic: 日志文档初始化
- Changes: 新建 `WORKLOG.md`，作为后续开发过程日志
- Files: `WORKLOG.md`
- Reason: 为接下来的模型升级、测试验证和问题追踪提供统一记录位置
- Verification: 文件已创建，模板可用于持续追加记录
- Follow-up: 后续每次实质性改动后追加一条日志

## 2026-03-16 15:10
- Topic: Phase 1 首轮传播模型升级
- Changes: 在 `config.py` 中新增个体异质性、平台推荐曝光和局部传播影响参数；在 `model.py` 中为每个单元生成活跃度、兴趣匹配度、影响力和疲劳阈值，拆分社交曝光与平台推荐曝光，并记录相关统计指标
- Files: `config.py`, `model.py`, `WORKLOG.md`
- Reason: 按 `PLAN.md` 的 Phase 1 路线，先在不改变整体使用方式的前提下提高传播模型拟真度
- Verification: 已通过源码编译检查；实际运行仍受当前 mac 环境缺少 `numpy` 依赖阻塞
- Follow-up: 在目标解释器中补齐 `numpy`/`matplotlib` 后执行完整运行验证，并决定是否把新增统计项接入可视化

## 2026-03-16 15:28
- Topic: 新增统计项接入可视化
- Changes: 扩展 `visualize.py` 的统计图布局，将社交曝光、推荐曝光、双重曝光、平均邻居传播强度和平均邻居影响力纳入展示
- Files: `visualize.py`, `WORKLOG.md`, `markdown.md`
- Reason: 让 Phase 1 新增的统计指标能够直接被观察和解释，避免模型升级后信息只保留在内部数据结构中
- Verification: 已通过源码编译检查，并在 `first_pyenv` 环境下完成入口运行验证；新增图表字段未出现键名或绘图错误
- Follow-up: 后续如需提升展示效果，可进一步调整子图配色、线型和布局密度

## 2026-03-16 16:00
- Topic: 状态链细化与统计口径升级
- Changes: 将状态链扩展为 `UNSEEN -> EXPOSED -> VIEWED -> ENGAGED -> SHARING -> INACTIVE`；把模型中的阶段权重和经验系数统一收口到 `config.py`；新增曝光量、观看转化率、互动率、分享率、传播深度等统计指标，并更新入口摘要和可视化展示
- Files: `config.py`, `model.py`, `visualize.py`, `main.py`, `WORKLOG.md`, `markdown.md`
- Reason: 按 `PLAN.md` 继续推进 Phase 1，使传播漏斗更细、参数更可调、输出更完整
- Verification: 已通过源码编译、人口守恒检查、历史长度一致性检查和 `first_pyenv` 环境下的完整入口运行验证；测试中发现“初始传播者被计入新增传播者”导致整体分享率口径偏差，已修正
- Follow-up: 当前参数下累计转化率接近 100%，后续可继续调低推荐或阶段转化参数，让漏斗分层更加明显

## 2026-03-16 16:18
- Topic: 切换到平衡版参数配置
- Changes: 将 `config.py` 中的平台推荐、观看、互动、分享以及对应热度/邻居加成参数下调到平衡版方案，目标是削弱推荐主导和过强的阶段转化
- Files: `config.py`, `WORKLOG.md`
- Reason: 让传播漏斗从“几乎全通过”调整为“有明显层次但仍保持可传播”
- Verification: 已通过源码编译和 `first_pyenv` 环境下的完整运行验证；程序正常运行，峰值传播人数从 5743 降到 5302、热度峰值出现步数从 17 延后到 28，但最终触达仍为 6400，整体观看/互动/分享转化率仍接近 100%，传播深度仍为 1
- Follow-up: 当前平衡版只实现了“传播降温”，尚未实现“漏斗明显分层”；下一步应继续下调推荐和阶段转化参数，或改进传播深度统计口径

## 2026-03-16 16:26
- Topic: 切换到强分层版参数配置
- Changes: 进一步下调 `P_RECOMMEND`、`P_VIEW`、`P_ENGAGE`、`P_SHARE` 及对应热度/邻居加成，使推荐链路更弱、行为漏斗更严格
- Files: `config.py`, `WORKLOG.md`
- Reason: 在平衡版仍未形成明显分层的情况下，继续增强漏斗筛选效果
- Verification: 已通过源码编译和 `first_pyenv` 环境下的完整运行验证；程序正常运行，峰值传播人数进一步降到 5066、热度峰值出现步数进一步延后到 39，但最终触达仍为 6400，整体观看/互动/分享转化率仍接近 100%，传播深度仍为 1
- Follow-up: 当前强分层版仍未形成真正的最终分层，说明仅靠参数调优已接近现有模型结构上限；后续应优先考虑在机制层加入阶段流失、停留或回落逻辑

## 2026-03-16 17:02
- Topic: 引入中间阶段流失机制
- Changes: 在 `model.py` 中为 `EXPOSED`、`VIEWED`、`ENGAGED` 加入“前进 / 停留 / 流失”三分机制，新增流失参数、累计漏斗统计、社交深度与推荐触达统计，并同步更新 `main.py`、`visualize.py` 与 `markdown.md`
- Files: `config.py`, `model.py`, `main.py`, `visualize.py`, `WORKLOG.md`, `markdown.md`
- Reason: 解决单纯调参无法让最终漏斗分层的问题，让中间状态不再几乎必然前进到下一层
- Verification: 已通过源码编译、人口守恒检查、历史长度一致性检查和 `first_pyenv` 环境下的完整入口运行验证。机制首次引入后传播被压得过弱，随后回调了 `config.py` 中的前进概率、流失概率和保护项。当前结果为：`Peak sharing users = 478`、`Overall view conversion rate = 51.74%`、`Overall engagement rate = 42.40%`、`Overall share rate = 61.15%`、`Overall skip rate = 48.26%`、`Overall view drop rate = 57.60%`、`Overall engage drop rate = 38.85%`
- Follow-up: 漏斗分层目标已基本达到，但 `max_social_depth` 仍停留在 1；后续应优先继续分析社交深度统计口径，或进一步减弱推荐覆盖速度以观察更深层传播

## 2026-03-16 17:22
- Topic: 实现 B 档最短停留步数机制
- Changes: 在 `config.py` 中新增 `MIN_EXPOSED_STEPS`、`MIN_VIEWED_STEPS`、`MIN_ENGAGED_STEPS`；在 `model.py` 中为 `EXPOSED`、`VIEWED`、`ENGAGED` 增加阶段计时器，并在达到最短停留步数前禁止前进或流失
- Files: `config.py`, `model.py`, `WORKLOG.md`, `markdown.md`
- Reason: 解决传播过程在前几十步内过快趋稳的问题，让中间状态形成更明显的平台期
- Verification: 已通过源码编译、人口守恒检查、历史长度一致性检查和 `first_pyenv` 环境下的完整入口运行验证。结果显示：`Peak Heat Step` 从 32 延后到 38，`Peak sharing users` 从 478 降到 389，`peak_exposed = 1702`、`peak_viewed = 1018`、`peak_engaged = 355`，整体转化率仍保持分层状态
- Follow-up: B 档已实现“节奏放缓”，但幅度有限，系统仍在较早阶段完成主要变化；后续可优先尝试继续提高最短停留步数，或结合 A 档继续减缓推荐速度

## 2026-03-16 17:35
- Topic: 结合 A 档继续放缓传播节奏
- Changes: 在保留 B 档最短停留机制的前提下，下调 `INITIAL_SHARERS`、`P_RECOMMEND`、`HEAT_BOOST_RECOMMEND`，并将 `MIN_EXPOSED_STEPS`、`MIN_VIEWED_STEPS` 进一步上调
- Files: `config.py`, `WORKLOG.md`, `markdown.md`
- Reason: 进一步延后峰值出现时间，避免系统在前几十步内过快趋稳
- Verification: 已通过源码编译、人口守恒检查和 `first_pyenv` 环境下的完整入口运行验证。结果显示：`Peak Heat Step` 从 38 延后到 47，`Peak sharing_step` 到 44，`Peak sharing users` 从 389 下降到 370，`Recommended reach` 从 423 降到 335；整体转化率仍保持分层状态，没有退回到“全通过”模型
- Follow-up: 本轮已明显放缓传播节奏，但系统仍在较早阶段完成主体扩散；若后续还要继续拉长生命周期，可优先继续上调 `MIN_EXPOSED_STEPS` / `MIN_VIEWED_STEPS`，或再轻微下调社交曝光起点

## 2026-03-16 17:48
- Topic: 继续延后传播峰值
- Changes: 进一步下调 `P_EXPOSE`，并把 `MIN_EXPOSED_STEPS`、`MIN_VIEWED_STEPS`、`MIN_ENGAGED_STEPS` 再次上调，目标是在保留漏斗分层的同时继续拉长传播前中期
- Files: `config.py`, `WORKLOG.md`, `markdown.md`
- Reason: 上一轮虽然明显延后了峰值，但主体扩散仍发生得偏早，需要继续压低社交曝光起点并延长中间状态停留
- Verification: 已通过源码编译、人口守恒检查和 `first_pyenv` 环境下的完整入口运行验证。结果显示：`Peak Heat Step` 从 47 延后到 51，`Peak sharing_step` 从 44 延后到 48，`Peak sharing users` 从 370 下降到 357；整体转化率保持稳定分层，`Recommended reach` 为 352
- Follow-up: 当前方案已经进一步放缓节奏且保持了漏斗分层，但系统仍在前段完成主体扩散；如果还要继续拉长生命周期，下一步应优先提高 `MIN_EXPOSED_STEPS` / `MIN_VIEWED_STEPS` 到更高档位，或开始评估 C 档累积意愿分数机制

## 2026-03-16 19:05
- Topic: 实现分组消融实验
- Changes: 新增 `ablation.py`，按 `ABLATION_EXPERIMENT_PLAN.md` 实现 `baseline`、`no_recommend`、`weak_social`、`no_heat_feedback`、`no_heterogeneity`、`no_dropout`、`no_stage_gating`、`slow_seed` 共 8 组实验；自动汇总核心指标并输出 `ablation_results.csv` 和 `ablation_delta.csv`；同步更新 `markdown.md` 说明新脚本、结果文件和运行方式
- Files: `ablation.py`, `WORKLOG.md`, `markdown.md`
- Reason: 为“不同影响因素对传播的重要性”提供可重复、可对比的实验入口，避免手工改参数逐组运行
- Verification: 已通过源码编译检查，并在 `first_pyenv` 环境中完成 `python my_cellM_project/ablation.py` 运行验证，成功生成两份结果表。当前结果已能区分主要机制作用：`no_heat_feedback` 使最终触达下降约 `63.64%`、热度峰值下降约 `99.17%`；`no_dropout` 使热度峰值上升约 `834.70%`、峰值传播人数上升约 `1046.22%`，且整体转化率重新接近 `100%`；`no_stage_gating` 使热度峰值时间提前 `16` 步并抬高峰值；`no_recommend` 对当前配置下的总体触达影响很小，但推荐触达归零
- Follow-up: 当前配置下“推荐”和“弱社交”对总体规模影响都不大，后续如果要让机制重要性更均衡，可继续检查推荐覆盖口径和社交链参数设计，或引入多随机种子重复实验

## 2026-03-16 19:22
- Topic: 新增消融结果绝对值柱状图
- Changes: 新增 `plot_ablation.py`，读取 `ablation_results.csv` 并绘制 `2 x 2` 的绝对值对比柱状图，覆盖最终触达人数、热度峰值、传播人数峰值和热度峰值出现步数；图标题和图例使用中文，输出文件为 `ablation_absolute.png`
- Files: `plot_ablation.py`, `WORKLOG.md`, `markdown.md`
- Reason: 让分组消融实验结果能够直接以图像方式比较，便于快速判断不同机制对传播规模、强度和节奏的影响
- Verification: 已通过源码编译检查，并在 `first_pyenv` 环境中完成 `python my_cellM_project/plot_ablation.py` 运行验证，成功生成 `ablation_absolute.png`。图像文件已生成且大小正常，可用于查看绝对值指标差异
- Follow-up: 下一步可继续补充相对变化图、漏斗对比图和热力图，形成完整的消融分析可视化输出

## 2026-03-16 19:48
- Topic: 扩展为多随机种子消融实验
- Changes: 将 `ablation.py` 从单随机种子版本扩展为多随机种子版本；新增 `SEEDS` 循环，输出逐次运行明细 `ablation_runs.csv`、按实验组聚合的 `ablation_summary.csv`，以及相对基准组的 `ablation_delta_summary.csv`；同时保留原有 `ablation_results.csv` 和 `ablation_delta.csv`，避免影响现有绘图脚本
- Files: `ablation.py`, `WORKLOG.md`, `markdown.md`
- Reason: 降低单一随机种子对结论的影响，让机制重要性判断从“单次样本”升级为“多次重复后的平均结果”
- Verification: 已通过源码编译检查，并在 `first_pyenv` 环境中完成 `python my_cellM_project/ablation.py` 运行验证。当前默认使用 5 个随机种子、8 个实验组，共生成 40 条逐次运行记录；`ablation_runs.csv` 行数为 `40`，`ablation_summary.csv` 和 `ablation_delta_summary.csv` 行数均为 `8`。关键指标的标准差已正常出现，例如基准组 `std_peak_heat = 319.620213`、`std_peak_sharing = 39.00641`，说明多随机种子聚合已生效。`no_heat_feedback` 的均值结果仍显著压低传播规模和强度，`no_dropout` 与 `no_stage_gating` 的均值结果仍明显抬高峰值并提前节奏；同时 `plot_ablation.py` 仍可正常读取保留的 `ablation_results.csv` 并生成图像
- Follow-up: 若多随机种子结果波动明显，下一步可把 `plot_ablation.py` 升级为读取 `ablation_summary.csv` 并加入误差棒

## 2026-03-16 20:02
- Topic: 升级绝对值柱状图为多随机种子版本
- Changes: 更新 `plot_ablation.py`，将数据源从 `ablation_results.csv` 切换为 `ablation_summary.csv`，在最终触达人数、热度峰值、传播人数峰值和热度峰值出现步数四个子图中加入标准差误差棒，并在柱顶额外标出 `±std`
- Files: `plot_ablation.py`, `WORKLOG.md`, `markdown.md`
- Reason: 让绝对值图不仅展示均值，还能直接反映不同实验组在多随机种子下的波动范围
- Verification: 已通过源码编译检查，并在 `first_pyenv` 环境中完成 `python my_cellM_project/plot_ablation.py` 运行验证，成功重新生成 `ablation_absolute.png`。图像已切换为读取 `ablation_summary.csv` 的版本，四个子图均正常显示均值柱体和标准差误差棒；例如基准组热度峰值显示为 `2734.0 ± 319.6`，`no_stage_gating` 的热度峰值出现步数显示为 `34.2 ± 1.8`，说明多随机种子汇总信息已成功接入图像
- Follow-up: 若误差棒版本可读性稳定，下一步可继续把相对变化图和漏斗图也切换到汇总表口径

## 2026-03-16 20:18
- Topic: 新增稳健热度节奏指标 `heat_center_step`
- Changes: 在 `ablation.py` 中新增 `heat_center_step` 统计，按热度时间重心公式 `sum(t * heat_t) / sum(heat_t)` 计算；将其接入单随机种子结果、多随机种子汇总和相对基准组对比输出
- Files: `ablation.py`, `WORKLOG.md`, `markdown.md`
- Reason: 解决 `no_heat_feedback` 组中 `peak_heat_step` 在低热度场景下过于依赖随机尖峰、方差过大的问题，为传播节奏分析提供更稳健的时间指标
- Verification: 已通过源码编译检查，并在 `first_pyenv` 环境中完成 `python my_cellM_project/ablation.py` 运行验证。`ablation_results.csv`、`ablation_summary.csv` 和 `ablation_delta_summary.csv` 已新增 `heat_center_step` 相关字段。对于重点关注的 `no_heat_feedback` 组，多随机种子下 `std_peak_heat_step = 150.909576`，而 `std_heat_center_step = 25.487004`，波动明显收敛；基准组 `std_heat_center_step = 2.251911`，与 `std_peak_heat_step = 2.167948` 同数量级，说明新指标在常规场景下也保持稳定可用
- Follow-up: 如果 `heat_center_step` 在 `no_heat_feedback` 组里明显比 `peak_heat_step` 稳定，下一步可把它加入后续节奏对比图或报告口径

## 2026-03-16 20:30
- Topic: 将 `heat_center_step` 接入绝对值对比图
- Changes: 更新 `plot_ablation.py`，在绝对值对比图中新增“热度时间重心步数”子图，并将整体布局从 `2 x 2` 调整为 `2 x 3`，同时保留 `peak_heat_step`，便于直接比较两种热度节奏指标
- Files: `plot_ablation.py`, `WORKLOG.md`, `markdown.md`
- Reason: 让对比图能够直观看到 `peak_heat_step` 与 `heat_center_step` 的差异，特别是用于解释 `no_heat_feedback` 组里原始峰值时间口径的不稳定性
- Verification: 已通过源码编译检查，并在 `first_pyenv` 环境中完成 `python my_cellM_project/plot_ablation.py` 运行验证，成功重新生成 `ablation_absolute.png`。图像已扩展为 5 个有效子图，新增“热度时间重心步数”后可直接与“热度峰值出现步数”对照；其中 `no_heat_feedback` 组在图中显示出 `peak_heat_step = 169.8 ± 150.9` 与 `heat_center_step = 228.0 ± 25.5` 的明显差异，说明新指标已经成功接入并改善了节奏解释的稳定性
- Follow-up: 若这张图的节奏部分可读性足够好，下一步可继续把相对变化图也接入 `heat_center_step`

## 2026-03-16 20:44
- Topic: 新增相对变化柱状图
- Changes: 更新 `plot_ablation.py`，新增读取 `ablation_delta_summary.csv` 的相对变化图输出 `ablation_delta.png`；图中加入最终触达人数、热度峰值、传播人数峰值、热度峰值出现步数和热度时间重心步数 5 个相对子图，百分比指标统一转换为 `%` 显示，并通过正负配色区分相对上升与下降
- Files: `plot_ablation.py`, `WORKLOG.md`, `markdown.md`
- Reason: 让多随机种子消融实验除了看绝对均值外，也能直接看相对基准组的变化幅度，便于判断不同机制对传播规模、强度和节奏的影响方向
- Verification: 已通过源码编译检查，并在 `first_pyenv` 环境中完成 `python my_cellM_project/plot_ablation.py` 运行验证，成功生成 `ablation_delta.png`。图像文件已生成且格式正常，5 个相对子图均可正常显示：例如 `no_heat_feedback` 组在图中表现为最终触达约 `-64.3%`、热度峰值约 `-98.9%`、热度峰值出现步数 `+117.6`、热度时间重心步数 `+170.7`；`no_dropout` 组则表现为热度峰值约 `+977.1%`、传播人数峰值约 `+1263.0%`
- Follow-up: 如果相对变化图可读性稳定，下一步可考虑再补一张漏斗结构相对变化图

## Template
- Topic:
- Changes:
- Files:
- Reason:
- Verification:
- Follow-up:
