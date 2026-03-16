# 分组消融实验实现说明

## 1. 目标

本说明文档给出一套适配当前项目结构的分组消融实验实现方案，用来分析不同影响因素对传播结果的重要性。

目标不是修改传播模型本身，而是在现有 `config + model + visualize` 结构之上增加一套实验驱动层，回答下面几个问题：

- 平台推荐对传播规模的重要性有多大
- 社交传播对传播深度和峰值的重要性有多大
- 热度反馈对传播节奏的重要性有多大
- 中间流失机制和最短停留机制对漏斗分层的重要性有多大
- 用户异质性是否显著改变结果

---

## 2. 实现原则

### 2.1 不改现有主流程接口

现有主入口仍然保持：

- `main.py` 用于单次运行
- `run_simulation(config)` 返回 `history, history_grids`

消融实验只是在此基础上新增一个实验脚本或实验模块，不替代现有入口。

### 2.2 实验通过“覆盖配置”实现

当前模型的主要控制项已经集中在 `config.py`，因此消融实验最适合的实现方式是：

1. 读取基准配置
2. 构造一组“配置覆盖项”
3. 在运行前生成实验专用配置对象
4. 用该配置对象调用 `run_simulation()`

这样不需要改 `model.py` 的函数签名。

### 2.3 结果统一表格化

每次实验只保留摘要级统计，不保存完整动画数据作为默认输出。

输出应优先是：

- 一张摘要结果表
- 一张相对基准组变化表

---

## 3. 建议新增文件

建议新增下面两个文件：

### `ablation.py`
负责定义实验组、构造实验配置、运行实验并汇总结果。

### `ablation_report.md` 或 `ablation_results.csv`
保存实验结果。

如果只保留一个结果文件，优先 `CSV`，因为更方便后续画图和比较。

---

## 4. 配置覆盖方案

建议不要直接修改 `config.py` 文件内容，而是新增一个“配置复制器”。

实现思路：

1. 从 `config` 模块里读取所有大写变量
2. 复制到一个新的轻量对象中
3. 用实验组的覆盖项替换其中部分字段

推荐接口：

```python
def build_experiment_config(base_config, overrides) -> object:
    ...
```

返回对象只需要支持：

`config.FIELD_NAME`

即可，因此可用：

- `types.SimpleNamespace`
  或
- 自定义简单类

---

## 5. 实验组定义

每个实验组建议用统一结构表示：

```python
{
    "name": "no_recommend",
    "description": "关闭平台推荐链路",
    "overrides": {
        "P_RECOMMEND": 0.0,
        "HEAT_BOOST_RECOMMEND": 0.0,
    },
}
```

建议第一批实验组如下。

### 5.1 基准组

```python
{
    "name": "baseline",
    "description": "当前配置",
    "overrides": {},
}
```

### 5.2 无推荐组

```python
{
    "name": "no_recommend",
    "description": "关闭平台推荐链路",
    "overrides": {
        "P_RECOMMEND": 0.0,
        "HEAT_BOOST_RECOMMEND": 0.0,
    },
}
```

### 5.3 弱社交传播组

```python
{
    "name": "weak_social",
    "description": "削弱社交传播影响",
    "overrides": {
        "P_EXPOSE": 0.03,
        "NEIGHBOR_VIEW_BOOST": 0.0,
        "NEIGHBOR_ENGAGE_BOOST": 0.0,
        "NEIGHBOR_SHARE_BOOST": 0.0,
    },
}
```

### 5.4 无热度反馈组

```python
{
    "name": "no_heat_feedback",
    "description": "关闭热度对行为的反向影响",
    "overrides": {
        "HEAT_BOOST_EXPOSE": 0.0,
        "HEAT_BOOST_VIEW": 0.0,
        "HEAT_BOOST_ENGAGE": 0.0,
        "HEAT_BOOST_SHARE": 0.0,
        "HEAT_BOOST_RECOMMEND": 0.0,
    },
}
```

### 5.5 无异质性组

```python
{
    "name": "no_heterogeneity",
    "description": "关闭用户个体差异",
    "overrides": {
        "ACTIVITY_STD": 0.0,
        "INTEREST_STD": 0.0,
        "INFLUENCE_STD": 0.0,
        "FATIGUE_THRESHOLD_MAX": 8,
        "FATIGUE_THRESHOLD_MIN": 8,
    },
}
```

### 5.6 无中间流失组

```python
{
    "name": "no_dropout",
    "description": "关闭中间阶段流失",
    "overrides": {
        "P_SKIP": 0.0,
        "P_DROP_VIEW": 0.0,
        "P_DROP_ENGAGE": 0.0,
        "INTEREST_DROP_WEIGHT": 0.0,
        "ACTIVITY_DROP_WEIGHT": 0.0,
    },
}
```

### 5.7 无停留门控组

```python
{
    "name": "no_stage_gating",
    "description": "关闭最短停留步数限制",
    "overrides": {
        "MIN_EXPOSED_STEPS": 1,
        "MIN_VIEWED_STEPS": 1,
        "MIN_ENGAGED_STEPS": 1,
    },
}
```

### 5.8 低种子组

```python
{
    "name": "slow_seed",
    "description": "降低初始传播源数量",
    "overrides": {
        "INITIAL_SHARERS": 1,
    },
}
```

---

## 6. 结果摘要函数

建议新增一个摘要函数，把 `history` 压缩成一行结果。

推荐接口：

```python
def summarize_history(history, config) -> dict:
    ...
```

建议输出字段如下。

### 6.1 传播规模指标

- `final_reached`
- `exposure_volume`
- `cumulative_views`
- `cumulative_engagements`
- `cumulative_shares`

### 6.2 峰值指标

- `peak_heat`
- `peak_heat_step`
- `peak_sharing`
- `peak_sharing_step`
- `peak_exposed`
- `peak_viewed`
- `peak_engaged`

### 6.3 漏斗指标

- `overall_view_conversion`
- `overall_engagement_conversion`
- `overall_share_conversion`
- `overall_skip_rate`
- `overall_view_drop_rate`
- `overall_engage_drop_rate`

### 6.4 来源与层级指标

- `recommended_reach`
- `max_social_depth`

### 6.5 节奏指标

- `steps_to_half_reach`
- `steps_to_half_peak_heat`

其中：

`steps_to_half_reach` 建议定义为累计触达人数第一次达到最终触达人数一半时的步数。

这个指标比只看峰值步数更能反映传播是否“展开得快”。

---

## 7. 实验运行主流程

建议主流程如下：

1. 加载基准配置
2. 定义实验组列表
3. 依次构造实验配置
4. 对每个实验组运行 `run_simulation()`
5. 调用 `summarize_history()` 生成摘要
6. 合并成总表
7. 计算相对基准组的变化比例
8. 保存结果文件

推荐伪代码：

```python
def run_ablation_suite():
    base = config
    groups = EXPERIMENT_GROUPS
    rows = []

    for group in groups:
        exp_config = build_experiment_config(base, group["overrides"])
        history, _ = run_simulation(exp_config)
        row = summarize_history(history, exp_config)
        row["group"] = group["name"]
        row["description"] = group["description"]
        rows.append(row)

    df = make_dataframe(rows)
    df_delta = compare_with_baseline(df)
    save_results(df, df_delta)
```

---

## 8. 基准对比规则

建议把 `baseline` 作为所有实验组的比较参照。

推荐新增一个变化表：

- `delta_final_reached_pct`
- `delta_peak_heat_pct`
- `delta_peak_sharing_pct`
- `delta_peak_heat_step`
- `delta_peak_sharing_step`
- `delta_overall_view_conversion_pct`
- `delta_overall_engagement_conversion_pct`
- `delta_overall_share_conversion_pct`

变化百分比建议定义为：

`(experiment - baseline) / baseline`

对于步数差值，可以直接保存绝对差：

`experiment_step - baseline_step`

---

## 9. 结果文件格式

建议输出两份结果：

### 9.1 `ablation_results.csv`

每一行一个实验组，每一列一个摘要指标。

### 9.2 `ablation_delta.csv`

每一行一个实验组，每一列一个相对基准组变化指标。

如果只输出一个文件，也可以把 `delta_` 字段一起合并进总表。

---

## 10. 可视化建议

第一版不建议复用当前 `visualize.py`，而是单独做实验结果图。

推荐最少画 3 张图：

### 图 1：传播规模对比

横轴：实验组  
纵轴：

- `final_reached`
- `peak_sharing`
- `peak_heat`

### 图 2：漏斗结构对比

横轴：实验组  
纵轴：

- `overall_view_conversion`
- `overall_engagement_conversion`
- `overall_share_conversion`
- `overall_skip_rate`

### 图 3：传播节奏对比

横轴：实验组  
纵轴：

- `peak_heat_step`
- `peak_sharing_step`
- `steps_to_half_reach`

---

## 11. 结果解释模板

实验跑完后，建议按下面规则解释。

### 推荐机制重要

如果 `no_recommend` 组显著降低：

- `final_reached`
- `peak_heat`
- `recommended_reach`

说明平台推荐是传播规模的重要驱动。

### 社交传播重要

如果 `weak_social` 组显著降低：

- `peak_sharing`
- `max_social_depth`

说明社交链路是传播扩散的重要驱动。

### 流失机制重要

如果 `no_dropout` 组显著提高：

- 各阶段整体转化率
- 峰值传播人数

说明中间流失机制是漏斗分层的关键来源。

### 停留门控重要

如果 `no_stage_gating` 组显著提前：

- `peak_heat_step`
- `peak_sharing_step`

说明最短停留机制是放缓传播节奏的重要来源。

### 异质性重要

如果 `no_heterogeneity` 组显著改变：

- 峰值位置
- 漏斗转化率
- 热度曲线形态

说明用户个体差异对系统行为有显著贡献。

---

## 12. 推荐实施顺序

建议按下面顺序落地。

### 第一轮

只做：

- `baseline`
- `no_recommend`
- `no_dropout`
- `no_stage_gating`
- `no_heterogeneity`

这是最小可用版本。

### 第二轮

补上：

- `weak_social`
- `no_heat_feedback`
- `slow_seed`

这样基本就能覆盖当前项目的主要影响因素。

### 第三轮

如果需要更严格分析，再增加：

- 多随机种子重复实验
- 对最关键组再做单因素敏感性分析

---

## 13. 验收标准

这套消融实验完成后，至少应能明确回答：

1. 哪一组机制对传播规模最重要
2. 哪一组机制对传播节奏最重要
3. 哪一组机制对漏斗分层最重要
4. 当前模型更依赖推荐，还是更依赖社交传播

如果这些问题仍然回答不清，说明实验分组不够好，或者摘要指标不够区分不同机制的作用，需要进一步补充实验指标。
