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

## Template
- Topic:
- Changes:
- Files:
- Reason:
- Verification:
- Follow-up:
