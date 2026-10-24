# Release Notes

## 20261025

> **发行方式变更：客户需要在本地自行生成 MJCF 和 USD。**
> **本版本起不再提交或随 Git 分发预生成的 `mjcf/`、`usd/`；克隆后不会包含这两类文件。**
> 仓库提供 URDF、mesh/纹理及完整转换工具。运行 `./convert_all_urdf_to_mjcf.sh`
> （默认 `--method urdf`）或 `./convert_all_urdf_to_usd.sh`（默认 `--flatten`），无需填写转换参数。
> USD 转换前须配置并激活 Isaac Lab / Isaac Sim 环境，详见 [转换指南](CONVERSION.md)。
> **Breaking distribution change: MJCF and USD must now be generated locally; prebuilt outputs are no longer shipped in Git.**

- 公开两个无参数批量转换入口及其全部 Python 依赖文件，自动定位模型目录并使用当前 Python 环境；补充依赖检查、失败退出状态和客户安装说明。当前版本无需 `git lfs pull`，旧版本的历史 LFS 对象仍保留。
- 新增 Revo3 MT 触觉版本，覆盖左右独立手、RevoArm 左单臂/右单臂/双臂及 RevoTron 左单臂/右单臂/双臂，共 8 个 URDF 模型，可在本地生成对应 MJCF/USD。Revo3 现提供普通版（无后缀）、MX（`_mx_touch`）和 MT（`_mt_touch`）三种版本。
- 更新 MX 触点位置，将可视触点半径统一为 1.8 mm；保留已与 SDK 核对的右拇指 fingerpad 编号关系，交换新点位的 18/20、19/21。MT 保留发布模型的触点及子点层级。
- 清理手模型固定关节上无效的 `axis` 和 `mimic` 标签。实体几何、质量、惯量、碰撞模型及活动关节参数保持一致。
- **接口名称变更：** RevoTron 双臂模型在 URDF、MJCF 和 USD 中统一使用 `waist_pitch_joint`、`neck_yaw_joint`、`head_pitch_joint`，替代原来的 `waist_pitch_Joint`、`neck_yaw_Joint`、`head_pitch_Joint`。下游按名称访问这些关节的配置或代码需要同步更新。
- 公开模型增至 29 个 URDF；默认 MJCF 转换保留 URDF 惯量，默认 USD 转换采用展平及既有 v4 碰撞/物理设置。生成文件保留在客户本地，并由 Git 忽略。
- 已在不含预生成文件的公开仓库副本中，从其他目录无参数运行两个入口：29 个 MJCF、29 个 USD 全部成功。MJCF 与已验证产物逐字节一致，USD 场景内容一致（忽略生成路径记录）；11 项回归检查通过。
- 已验证模型树、资产引用、三版本装配、SDK 点位映射、MuJoCo 加载及前向计算、USD 展平和触点位置。已有 1,210 个 mesh/纹理文件保持逐字节一致。本次未更新预览图，也未进行真实机器人或动力学精度验证。

## 20261014

- 添加指尖压阻触点坐标
- 修复左右手惯量不一致问题
- 修改link命名拼写错误

## 20261009

- 优化了revo3外观

## v2026.10.05

### Appearance

- Make the approved 2026-09-20 Revotron metallic-paint appearance the default for single-arm and bimanual Revo3 assemblies, including MX Touch variants, using the existing URDF filenames.
- Add silver shells, dark gray trim, cyan light covers, logos, a static face expression, rear-head rainbow details, column markings, and control-panel details.
- Replace the original base, chest, and head visual meshes with 62 split and decorative meshes. Preserve Revotron joint, inertial, and collision definitions.
- Refresh Revotron URDF previews and add appearance detail views and a MuJoCo preview.

### Model exports

- Regenerate the public URDF, MJCF, and USD assets from the upstream description packages, with appearance definitions maintained in the source packages for future generation.
- Preserve global and inline URDF colors in MJCF, retain tactile marker primitives, and use shell inertia for decorative surface meshes so they load in MuJoCo.
- Regenerate USD with v4 settings: fixed bases, merged fixed joints, zero drive stiffness/damping, disabled gravity, self-collision, and 16/4 position/velocity solver iterations. Retain the Revo3 palm decomposition and 32 thumb collision hulls per hand.
- Preserve USD visual material colors and export flattened, non-instanced assets without unresolved importer references.
- Store the two bimanual Revotron USD files with Git LFS; run `git lfs pull` after cloning to retrieve the model data.

### Validation

- Validate all 21 public model sets: load MJCF in MuJoCo, reopen USD, compare visual geometry and colors with URDF, and check the USD physics settings. These checks cover loading and exported properties; they do not add new dynamics or collision-accuracy validation.

## v2026.09.30

- Update both Revo3 hands with 32 trimmed thumb CMR collision meshes per hand and backtrimmed palm collision meshes.
- Propagate the collision geometry to Revo3, RevoArm, and Revotron URDF, MJCF, and USD models.

### Appearance

- Revotron: Revotron-basic new ID.
- Revo3: Revo3 MX Touch / basic silver version.
- Revomate/arm: ID not yet updated.
- Revo2: Product version.

### Kinematics

- Revotron: Validated.
- Revo3: Validated.
- Revomate/arm: Validated.
- Revo2: Validated.

### Dynamics

- Revotron: Validated.
- Revo3: Validated.
- Revomate/arm: Not yet validated.
- Revo2: Validated.

### Collision

- Revotron: Not yet processed.
- Revo3: Self-collision fixes added; validation pending.
- Revomate/arm: Not yet processed.
- Revo2: Not yet processed.

## v2026.09.29

- Add Revotron camera coordinate frames and wrist cameras.
- Add head OAK and left/right wrist camera meshes, with updated mounting transforms and inertial properties.
- Update Revotron wrist connectors and the corresponding URDF, MJCF, and USD models.

## v2026.09.26

- Add Revo3 MX touch and without-touch model variants.
- Fix Revo3 inertia parameters using legacy mass properties transformed into the updated link frames.
- Fix Revo3 MPR joint definitions.
- Add Revo3 appearance materials and updated previews.
- Revo3 collision meshes are not yet processed in this version.
- Add the RevoTron ID appearance.
