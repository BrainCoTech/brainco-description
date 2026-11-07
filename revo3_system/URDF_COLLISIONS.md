# Revo3 右手 URDF 碰撞资产

入口为 [`urdf/revo3_right.urdf`](urdf/revo3_right.urdf)，采用已审核的显式凸包。
右手各变体及 RevoArm/RevoTron 组合模型的拇指 CMR 范围统一为
**0～106°**，即 **0～1.8500490071139892 rad**。

## 右手无触觉版参数

| 项目 | 数量 |
| --- | ---: |
| 凸块实例 | 144 |
| 唯一碰撞网格 | 90 |
| 唯一顶点 / 展开顶点 | 5,427 / 9,678 |
| 参与碰撞的源 link | 22 |
| 掌部凸块 / 顶点 | 42 / 1,790 |
| link / 活动关节 / 固定关节 | 58 / 21 / 36 |
| 原始可视网格 | 57 |

碰撞网格位于 [`meshes/hands/collision/right/optimized_20261027/`](meshes/hands/collision/right/optimized_20261027/)。
四指复用 MPR/MCP/PIP/DIP 网格，通过 collision origin 定位；掌胶承载 42 个凸块。
可视几何、关节原点/轴、质量与惯性保持源 URDF 定义。
右手 MX/MT、左手和组合模型的碰撞几何使用各自现有配置。

## 转换与检查

在仓库根目录执行：

```bash
# 生成 MJCF
python3 urdf_to_mjcf.py revo3_system/urdf/revo3_right.urdf

# 生成 USD；先激活 Isaac Lab / Isaac Sim 环境
python3 convert_urdf_v4.py revo3_system/urdf/revo3_right.urdf revo3_system/usd/revo3_right.usd --headless --flatten

# 完整性检查
python3 revo3_system/tools/verify_optimized_urdf.py

# MuJoCo 姿态与 USD 导入检查
python3 revo3_system/tools/verify_optimized_urdf.py --runtime --usd revo3_system/usd/revo3_right.usd
```

USD 对每块网格使用 `convexHull`，PhysX 顶点上限为 255，Newton `maxHullVertices=-1`。
MJCF 按文件路径复用网格。可直接加载的 MJCF/USD 位于
[`optimized/right_20261027/`](optimized/right_20261027/README.md)。

当前验证结果：[21 关节限位与零位保持检查](validation/right_joint_limits_20261107.json)、
[URDF/MJCF 碰撞等价性](validation/right_urdf_limits_20261107.json)。
2026-11-02 与 2026-11-04 的检查记录保留各自当时限位，作为历史验证结果。
验证环境为 MuJoCo 3.12.0、Newton 1.6.1、Isaac Lab 3.0 / Isaac Sim 6.2。
共享文件数量不等于仿真器运行时 mesh 对象数量。

## 执行器与维护

运行时需显式配置执行器力矩上限；URDF 的 `effort="0"` 不是可用的控制参数。
辨识参数及示例见 [`parameters/`](parameters/README.md)。
直接用 Newton 导入 URDF 时，设置 `mesh_maxhullvert=-1`、`parse_visuals_as_colliders=False`。

`tools/sync_optimized_collisions.py` 可从审核包重新写入凸包，并保留当前关节限位。
仅在需要恢复审核版碰撞时执行。
