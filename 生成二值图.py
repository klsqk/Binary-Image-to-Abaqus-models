import numpy as np
from scipy.ndimage import gaussian_filter
from scipy.stats import norm
from scipy.optimize import minimize_scalar
import matplotlib.pyplot as plt

# 参数设置
Nx, Ny = 100, 100       # 网格尺寸
lambda_x, lambda_y = 5, 3  # 特征长度
target_porosity = 0.2   # 孔隙率

# 生成高斯随机场（标准化版本）
def generate_gaussian_field():
    white_noise = np.random.normal(size=(Ny, Nx))
    sigma_x = lambda_x / np.sqrt(2)
    sigma_y = lambda_y / np.sqrt(2)
    Z = gaussian_filter(white_noise, sigma=(sigma_y, sigma_x), mode='wrap')
    return (Z - Z.mean()) / Z.std()  # 标准化

# 优化阈值函数
def find_optimal_threshold(Z, target):
    def loss(F0):
        porosity = (Z <= F0).mean()  # 黑色区域占比
        return abs(porosity - target)
    
    result = minimize_scalar(loss, bracket=[-3, 3])
    return result.x

# 主流程
np.random.seed(None)  # 随机种子
Z = generate_gaussian_field()
F0 = find_optimal_threshold(Z, target_porosity)
binary_map = (Z > F0).astype(int)  # 1=材料，0=孔隙

# 可视化结果
plt.figure(figsize=(10, 4))

# 高斯随机场原图
plt.subplot(1, 2, 1)
plt.imshow(Z, cmap='jet', origin='lower', 
          extent=[0, Nx, 0, Ny])
plt.colorbar(label='Field Intensity')
plt.title('Gaussian Random Field')

# 二值图
plt.subplot(1, 2, 2)
plt.imshow(binary_map, cmap='gray', origin='lower',
          extent=[0, Nx, 0, Ny])
plt.title(f'Binary Map\n(Porosity: {(binary_map == 0).mean():.2f})')

plt.tight_layout()
plt.show()

# 保存二值图数据（ASCII格式）
np.savetxt('porosity.txt', binary_map, fmt='%d', delimiter='')