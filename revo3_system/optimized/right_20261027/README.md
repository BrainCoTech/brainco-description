# Revo3 右手优化碰撞资产

本目录提供 **Revo3 右手无触觉标记版**的已验证资产，包含可直接加载的 **MuJoCo MJCF** 和 **Newton / Isaac Lab / PhysX 共用 USD**。本版优化了掌胶、拇指及四指的碰撞几何，保留原始可视模型的顶点、法线、面和材质。

版本：**2026-10-27**。共 **144 个凸块实例、90 份唯一碰撞网格、5,427 个唯一顶点**。本目录作为独立资产包使用；仓库 `urdf/` 下的默认模型及批量转换脚本仍使用原来的碰撞配置，不会自动生成本版。

## 文件说明

```text
right_20261027/
├── revo3_right.xml                 # MuJoCo MJCF
├── revo3_right.usd                 # Newton、Isaac Lab / PhysX 共用
├── meshes_compact/                # 90 个有效凸包 OBJ
│   ├── right_palm_rubber_link/     # 掌部碰撞
│   ├── right_thumb_*_link/         # 拇指各段碰撞
│   └── MPR_sides/、MCP/、PIP/、DIP/ # 四指共享模板
├── visual_support/
│   └── right_palm_led_link.obj     # 原始屏幕 DAE 转成的 MJCF 可视网格
├── collision_manifest.json        # 网格、所属 link、共享变换及文件哈希
├── verify_assets.py               # 完整性与导入检查
├── SHA256SUMS                     # 本目录文件的 SHA-256 清单
└── validation/
    ├── source_validation.json     # 发布前的几何、间隙与运行验证摘要
    └── packaging.json             # 发布打包后的等价性与加载验证
```

**请保留整个 `revo3_system` 目录的相对结构。** MJCF 引用 [`../../meshes/hands/visual/`](../../meshes/hands/visual/) 中的原始可视网格；USD 已内嵌可视几何，但屏幕纹理仍引用该目录中的 `textures/revo3_screen.png`。只复制本文件夹或单独复制 XML/USD，可能缺少这些依赖。资源路径均为相对路径，无需原训练工程或 Git LFS 下载。

## 快速使用

以下命令和代码均以 **仓库根目录**为工作目录。文件完整性检查需要 Python 3.10 或以上；运行加载示例前，需使用已安装对应仿真库的 Python 环境。

### 1. 检查资产

```bash
# 只检查文件、SHA-256、依赖路径、网格和顶点数量；使用 Python 标准库
python revo3_system/optimized/right_20261027/verify_assets.py

# 额外检查 MuJoCo 与 USD 导入；需要 mujoco、numpy、pxr（OpenUSD）
python revo3_system/optimized/right_20261027/verify_assets.py --runtime
```

核对包括 README 在内的整个目录，可在本目录运行：

```bash
sha256sum --check SHA256SUMS
```

### 2. MuJoCo

直接加载 [`revo3_right.xml`](revo3_right.xml)：

```python
import mujoco

model = mujoco.MjModel.from_xml_path(
    "revo3_system/optimized/right_20261027/revo3_right.xml"
)
data = mujoco.MjData(model)
mujoco.mj_forward(model, data)
print("活动关节数：", model.njnt)  # 21
```

### 3. Newton / MuJoCo Warp

通过 Newton 导入 [`revo3_right.usd`](revo3_right.usd)，再由任务侧选择求解器；使用 MuJoCo Warp 时，无需另一份碰撞 USD。

```python
import newton

builder = newton.ModelBuilder()
builder.add_usd(
    "revo3_system/optimized/right_20261027/revo3_right.usd",
    floating=False,
    load_visual_shapes=False,
    load_static_visual_shapes=False,
    enable_self_collisions=True,
)
model = builder.finalize(device="cuda:0")
```

示例中的 `load_visual_shapes=False` 与 `load_static_visual_shapes=False` 用于 headless 训练时不加载可视形状。资产仍保留完整原始外观，查看时可按需要加载。

### 4. Isaac Lab / PhysX

直接使用同一份 [`revo3_right.usd`](revo3_right.usd)，无需重新执行 URDF 转换或凸分解。USD 的默认 prim 为 `/revo3_single`。

在已启动 Isaac Lab 仿真应用的脚本中，配置资产加载入口：

```python
from pathlib import Path
import isaaclab.sim as sim_utils

usd_path = Path(
    "revo3_system/optimized/right_20261027/revo3_right.usd"
).resolve()
spawn_cfg = sim_utils.UsdFileCfg(usd_path=str(usd_path))
# 将 spawn_cfg 作为任务中 ArticulationCfg 的 spawn 配置。
```

以上片段只配置资产入口。执行器、关节目标、场景放置、魔方和控制循环由任务侧配置；本目录不包含完整的抓持训练环境。

## 碰撞体参数

| 项目 | 数量 |
| --- | ---: |
| 凸块实例 | 144 |
| 参与碰撞的源 link | 22 |
| 唯一碰撞 OBJ | 90 |
| 唯一顶点 / 按实例展开顶点 | 5,427 / 9,678 |
| 掌部凸块 / 顶点 | 42 / 1,790 |
| 当前启用的球、胶囊、圆柱等标准碰撞体 | 0 |
| 原始可视网格 / 三角形 | 57 / 241,252 |
| 活动关节 | 21 |
| 90 个有效 OBJ 的文件总大小 | 381,728 字节，约 373 KiB |

各部位分配如下。四指模板每份几何复用 4 次，表中的“唯一顶点”只统计一份模板。

| 部位 | 唯一网格 | 凸块实例 | 唯一顶点 |
| --- | ---: | ---: | ---: |
| 掌胶 | 42 | 42 | 1,790 |
| 拇指 CMP | 5 | 5 | 355 |
| 拇指 CMR | 3 | 3 | 214 |
| 拇指 MCP | 3 | 3 | 501 |
| 拇指 PIP | 12 | 12 | 597 |
| 拇指 DIP | 7 | 7 | 553 |
| 四指共享 MPR | 2 | 8 | 124 |
| 四指共享 MCP | 3 | 12 | 457 |
| 四指共享 PIP | 7 | 28 | 425 |
| 四指共享 DIP | 6 | 24 | 411 |
| **合计** | **90** | **144** | **5,427** |

### 碰撞归属与共享变换

- 掌部碰撞归属 `right_palm_rubber_link`；掌壳、掌触面、腕部及附属件不额外启用独立碰撞体。
- 拇指由 CMP、CMR、MCP、PIP、DIP 五个 link 承载碰撞。
- 食指、中指、无名指、小指由各自的 MPR、MCP、PIP、DIP 承载碰撞。讨论时称为四指“CMR”的指根，在资产中的正式名称是 **MPR**。
- 指节胶皮等接触面的几何已并入对应承载 link，单独的 rubber/touch link 不重复添加碰撞。可视几何继续保留。

清单中的 owner 是源 link 名称。USD 合并固定关节后，源 link 与仿真刚体不一定一一对应，例如掌部几何可位于 `world` 刚体下；集成时应核对实际 USD 层级。

四指通过 `MPR_sides`、`MCP`、`PIP`、`DIP` 共享模板减少重复几何。清单内的 `template_to_owner` 是 **4×4 刚体变换矩阵**，按列齐次坐标计算：`p_owner = template_to_owner @ p_template`，平移单位为米。未使用共享模板的 owner 对应单位变换。迁移 OBJ 时必须同时应用这个变换，不能只替换文件名。

“唯一顶点”是几何去重后的统计，“展开顶点”是按每个碰撞实例累加的统计。运行时的实际共享和显存占用还取决于导入器及求解器的缓存，不能直接由文件顶点数推算。

### 凸包导入设置

USD 中的碰撞 API 直接设置在具体 mesh 上，每块使用 `convexHull`；共享几何通过内部 USD 引用组织。

| 设置 | 当前值 |
| --- | --- |
| Newton `newton:maxHullVertices` | `-1`，保留显式凸包顶点 |
| PhysX `physxConvexHullCollision:hullVertexLimit` | `255` |
| 已验证的最大凸多边形顶点数 | 37 |
| 已验证的最大顶点关联面数 | 14 |

本版已经完成凸分解与简化，再执行自动分解可能改变凸块数量和接触轮廓。

## 物理参数与验证结果

本资产保留审核时的工程物理配置，包括掌胶质量 **0.03825060230603083 kg** 及对应惯量覆盖，详见清单的 `physics.engineering_inertial_overrides`。这些参数不应直接用于覆盖仓库原始 URDF 的惯性字段。本轮几何优化没有新增显式刚体对排除规则；父子刚体过滤仍取决于仿真后端。

### 掌部与指根间隙

最后一轮仅对掌部第 9、10、19、41 块作局部斜切，避让食指和小指 MPR 的运动范围，同时保留掌胶主接触面和内弧。距离检查绕过了碰撞对过滤，以下为所检关节范围内的连续间隙保守下界：

| 与手掌相邻的部位 | 间隙下界，约 mm |
| --- | ---: |
| 食指 MPR | 0.205 |
| 中指 MPR | 3.307 |
| 无名指 MPR | 3.180 |
| 小指 MPR | 0.205 |
| 拇指 CMP | 1.755 |
| 拇指 CMR | 0.211 |

其他相邻关节内部仍可能保留合理重叠。这些结果不表示所有关节组合、所有自碰撞对均已无互穿。

### 已完成的验证

[`source_validation.json`](validation/source_validation.json) 记录发布前资产的哈希与验证摘要：掌胶表面和内弧检查、2,125 个根部/审核姿态、2,000 个弯指姿态，以及 MuJoCo、Newton MuJoCo Warp、PhysX 三后端各 **4 环境、250 控制步、5 秒**的刚体立方体持有检查。立方体边长 50 mm、质量 80 g。姿态扫描相对上一版没有新增接触对或穿透量增加。

[`packaging.json`](validation/packaging.json) 记录发布打包后的检查：归一化依赖路径和过时的 USD 文档元数据后，USD 内容与原审核版一致；MJCF 内容及 **480 项编译数值数组**一致；Newton 导入后的碰撞几何与放置一致；复制到独立目录后仍可加载。

发布加载检查使用 **MuJoCo 3.12.0、Newton 1.6.1、OpenUSD 26.8**；此前 PhysX 检查使用 **Isaac Lab 3.0.0 / Isaac Sim 6.2**。本版尚未重新测量 4,096 环境显存，也未在本目录提供任意控制策略下的稳定持有保证。

## 常见问题

**提示缺少 `OmniPBR.mdl`：** 这是 Isaac Sim / Omniverse 提供的渲染材质模块。普通 OpenUSD 环境可能无法解析它；headless Newton 无需该着色器。若缺少的是 OBJ、STL 或 PNG，请先检查上述相对目录是否完整。

**为什么 USD 和 XML 文件哈希不同于原审核目录：** 发布时修改了相对资源路径和过时的 USD 文档元数据，几何及物理参数保持一致。原审核版本与发布版本的哈希均记录在 [`collision_manifest.json`](collision_manifest.json) 中。

**为什么从默认 URDF 重新转换后不是这组碰撞体：** 本目录是独立保存的审核版本。默认 URDF 和转换脚本尚未接入该碰撞配置，使用本版时应直接加载这里的 XML/USD。

## 来源与适用范围

原始可视模型来自 [BrainCoTech/brainco-description](https://github.com/BrainCoTech/brainco-description) 提交 `6db7e2ed1d864ee0a3ab6ff62d43a303787137f6`；打包基线为 `da568324b86b74538dd1e08479103faa90dd9647`，两版所引用的可视文件字节一致。本资产通过 [PR #4](https://github.com/BrainCoTech/brainco-description/pull/4) 合并到仓库。

适用范围为右手无触觉标记版。左手、MX/MT 触觉标记版、RevoArm 和 RevoTron 装配模型需分别完成迁移与验证。后续迁入默认 URDF 时，需要保留原始惯性、正确转移每个凸块的所属 link 和局部变换，并确保转换器不再次分解或截断这些凸包。
