# Revo3 右手碰撞反向迁入 URDF

2026-11-01，`dev` 分支。入口为 [`urdf/revo3_right.urdf`](urdf/revo3_right.urdf)。
来源是此前审核的 [`optimized/right_20261027/`](optimized/right_20261027/README.md)，本次只替换碰撞定义。

## 参数与范围

| 项目 | 迁移后 |
| --- | ---: |
| 显式凸块 / URDF collision 元素 | 144 |
| 唯一 OBJ 网格 | 90 |
| 唯一顶点 / 按实例展开顶点 | 5,427 / 9,678 |
| 参与碰撞的源 link | 22 |
| 掌部凸块 / 顶点 | 42 / 1,790 |
| link / 活动关节 / 固定关节 | 58 / 21 / 36 |
| 原始可视网格 | 57，未修改 |

主分支原 URDF 是 82 个 mesh collision 元素，按仓库转换器载入 MuJoCo 为
119,082 个输入顶点；这些输入元素数不能当作 PhysX 自动分解后的凸包数。
新版以 144 个已经分解好的凸块表达轮廓，不再将整块掌体交给导入器自动分解。

本次仅迁移 **右手无触觉标记版**。MX/MT、左手、RevoArm、RevoTron 暂保留旧配置。
原始可视、材质、关节轴、限位、质量和惯性字段与 `9a5b7de` 基线一致。
审核快照中的工程惯性覆盖没有复制到 URDF；所以新 URDF 与旧快照的动力学参数不是完全相同的。

## 文件和变换

碰撞文件位于 [`meshes/hands/collision/right/optimized_20261027/`](meshes/hands/collision/right/optimized_20261027/)。
其 `collision_manifest.json` 记录网格哈希、顶点数、owner 和共享模板到 owner 的变换。
OBJ 保留原审核文件字节，只增加可识别的文件名。四指共享 MPR/MCP/PIP/DIP 共 18 份网格，
各个实例通过 `<collision><origin xyz="..." rpy="..."/>` 放到对应 link 坐标系。
米、弧度单位；旋转使用 URDF 固定轴 RPY（`Rz(yaw) Ry(pitch) Rx(roll)`）。

掌胶承载 42 块复合碰撞；拇指 CMP/CMR/MCP/PIP/DIP、四指 MPR/MCP/PIP/DIP 分别承载指部碰撞。
原有 rubber/touch、掌壳、腕部等 link 的独立碰撞被移除，可视和惯性保留。

## 转换与验证

在仓库根目录执行：

```bash
# URDF → MJCF；标准库即可生成，加载检查需要 MuJoCo
python3 urdf_to_mjcf.py revo3_system/urdf/revo3_right.urdf

# URDF → USD；先激活 Isaac Lab / Isaac Sim 环境
python3 convert_urdf_v4.py revo3_system/urdf/revo3_right.urdf \
  revo3_system/usd/revo3_right.usd --headless --flatten

# 标准库完整性检查
python3 revo3_system/tools/verify_optimized_urdf.py

# 重建 MJCF、比较 129 组姿态，并检查生成 USD；需 numpy/scipy/mujoco/pxr
python3 revo3_system/tools/verify_optimized_urdf.py --runtime \
  --usd revo3_system/usd/revo3_right.usd
```

`urdf_to_mjcf.py` 按文件路径、scale 和用途复用 mesh，实例变换留在 geom 上。
转换后的 MJCF 为 144 个碰撞 geom、90 个 mesh 定义；碰撞 `maxhullvert=-1`。
USD 转换器识别 `revo3_opt_` 显式凸块，自动使用逐块 `convexHull`，即使基础选项仍为
`convex_decomposition` 也不会重新分解这些凸块。实际 mesh 上设置 PhysX 顶点上限 255、
Newton `maxHullVertices=-1`。旧左手等 v4 配置仍保留掌体分解和 32 个 CMR 凸块的规则。

本次验证环境：MuJoCo 3.12.0、Newton 1.6.1、Isaac Lab 3.0.0 / Isaac Sim 6.2、OpenUSD 26.8。
Isaac Lab 2.x 接口分支保留；这轮没有重新运行 2.x。
导入器 3 的层级、参数名、输出路径及线性颜色存储与旧版不同，转换脚本已作适配，
并恢复了导入器未填入的屏幕纹理路径。原始可视网格没有简化。

验证结果见 [`validation/right_urdf_20261101.json`](validation/right_urdf_20261101.json)：

- 129 组关节姿态下，新 URDF → MJCF 与审核快照的碰撞顶点偏差小于 `2e-7 m`（实测约 `5.1e-15 m`）。
- 新 USD 的 144 个凸块、90 组唯一顶点数组、9,678 个展开顶点及逐块放置检查通过；
  相对 MJCF 的最大顶点偏差约 `5.2e-8 m`，来自浮点导入精度。
- USD 原始 57 份可视网格的颜色和屏幕纹理检查通过；左手旧 v4 转换回归检查通过。

这次是格式迁移和几何检查，没有重做 4,096 环境显存或稳定抓持测试。
90 份共享文件不保证每个导入器只创建 90 个运行时 mesh 对象；Newton 1.6.1 导入检查仍创建 144 个对象。

## Newton 使用注意

直接导入 URDF 时，应传 `mesh_maxhullvert=-1`，并使用 `parse_visuals_as_colliders=False`。
Newton 1.6.1 将 URDF 网格读为 `MESH`，经本仓库生成的 USD 则读为显式 `CONVEX_MESH`；
需要 Newton 原生凸包语义时优先采用生成的 USD。

原 URDF 的 21 个活动关节保留 `effort="0"`。Newton 的 MuJoCo 求解器可能因此报告
`actfrcrange[0] should be smaller than actfrcrange[1]`。任务侧应配置实际执行器力矩上限，
不要把本次几何迁移当作控制参数修复。几何导入测试只在内存中临时放开了零力矩限制，未改动资产。

## 复现初次迁移

`python3 revo3_system/tools/sync_optimized_collisions.py` 可从冻结的 20261027 审核包重建本次碰撞。
脚本会检查非碰撞字段的基线哈希，保留四指共享变换。后续在 `dev` 手工优化碰撞后，
除非确实要恢复到这次审核版本，否则不要重新执行该同步命令。
