GRID_SIZE = 80
STEPS = 500
RANDOM_SEED = 22

#初始传播源数量
INITIAL_SHARERS = 5

#领域类型
NEIGHBORHOOD = "von_neumann"

#基础传播参数
P_EXPOSE = 0.11     #未接触用户被邻居影响而看到视频的基础概率
P_SHARE = 0.22      #已观看用户转变为传播者的基础概率
P_FADE = 0.08       #传播者失去兴趣的基本概率

#热度反馈参数
HEAT_BOOST_EXPOSE = 0.002   #热度对曝光概率的提升
HEAT_BOOST_SHARE = 0.0018   #热度对分享概率的提升
HEAT_DECAY = 0.92           #热度衰减系数

#热度计算
HEAT_FROM_SHARES = 1.0
HEAT_FROM_NEW_SHARES = 2.0

#传播者最长持续步数
MAX_SHARING_STEPS = 8

#可视化
INTERVAL = 150  #ms