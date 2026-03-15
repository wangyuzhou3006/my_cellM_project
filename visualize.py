import numpy as np
from matplotlib import pyplot as plt
from matplotlib import animation
from matplotlib.colors import ListedColormap

from model import UNSEEN, VIEWED, SHARING, INACTIVE

#显示整个传播过程的网格动画
def show_animation(history_grids, interval = 150):  #interval:每帧间隔多少毫秒
    #定义颜色映射
    cmap = ListedColormap([
        '#ffffff', # UNSEEN
        '#8ecae6', # VIEWED
        '#e63946', # SHARING
        '#9aa0a6', # INACTIVE
    ])
    
    #创建图像
    fig, ax = plt.subplots(figsize = (6,6)) #创建画布和坐标轴
    im = ax.imshow(history_grids[0], cmap = cmap, vmin=0, vmax=3, animated=True) #显示图像
    ax.set_title("Short Video Diffusion")
    #去掉坐标刻度
    ax.set_xticks([])
    ax.set_yticks([])
    
    #定义动画更新函数
    def update(frame):
        im.set_array(history_grids[frame])
        ax.set_title(f"Short Video Diffusion - step {frame}")
        return [im]     #返回需要刷新的图像对象
    
    #创建动画对象
    ani = animation.FuncAnimation(
        fig,                                #做动画的图
        update,                             #每一帧都调用更新函数
        frames = len(history_grids),        #总帧数就是历史网格数
        interval = interval,                #interval控制播放速度
        blit=True,                          
        repeat=False,                       #不循环
    )
    
    plt.show()
    return ani

#统计曲线绘制
def plot_metrics(history):
    #时间轴
    t = np.arange(len(history["heat"]))
    #创建两个子图
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))     #绘制一行两列的图，左边：状态人数变化，右边：热度和新增传播
    #左图
    axes[0].plot(t, history["unseen"], label="Unseen")
    axes[0].plot(t, history["viewed"], label="Viewed")
    axes[0].plot(t, history["sharing"], label="Sharing")
    axes[0].plot(t, history["inactive"], label="Inactive")
    axes[0].set_title("State Counts")
    axes[0].set_xlabel("Step")
    axes[0].set_ylabel("Number of Users")
    axes[0].legend()
    #右图
    axes[1].plot(t, history["heat"], label="Heat")
    axes[1].plot(t, history["new_shares"], label="New Shares")
    axes[1].set_xlabel("Step")
    axes[1].legend()
    
    plt.tight_layout()
    plt.show()