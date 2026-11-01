# Revo3 PACE 辨识参数（2026-11-02）

本目录随 `dev` 附上提供的参数包，原始文件逐字节保留。
辨识工程为 [REVO3_PACE](https://github.com/tannjieee/REVO3_PACE)，
包内记录的匹配提交为 `936c813d45fca85a18ce366b6640cf1f1dceb005`。

| 入口 | 内容 |
| --- | --- |
| [原始 ZIP](Revo3_PACE_parameters_20261102.zip) | 完整交付包，413,960 字节 |
| [SHA256SUMS](SHA256SUMS) | 原始 ZIP 的 SHA-256 |
| [解压内容](pace_20261102/) | 与 ZIP 内的 24 份文件完全一致，可直接读取 |
| [完整使用说明](pace_20261102/README_使用说明.txt) | 字段、单位、控制形式、时间尺度、回放方法及适用范围 |
| [参数总览 HTML](pace_20261102/参数总览.html) | 下载后用浏览器打开，查看逐关节参数和图表 |
| [本次附包检查](../validation/pace_bundle_20261102.json) | 文件一致性、模型加载和当前 URDF 限位差异 |

## 选择参数

| 模型 | 状态 | 参数文件 |
| --- | --- | --- |
| `fit_03` | 原全关节冻结基线，默认使用 | [best_parameters.json](pace_20261102/models/fit_03/best_parameters.json) |
| `balanced` | 七参数修正候选，尚未替代基线 | [best_parameters.json](pace_20261102/models/balanced/best_parameters.json) |

两套均为完整的 21 关节参数，不需要叠加。
[model_differences.json](pace_20261102/model_differences.json) 记录七处改动的完整精度。
`balanced` 改善了部分目标瞬态，但共同时间窗的全手 4 Hz RMSE 从 1.1637° 增至
1.3520°；包内没有新的独立验证，因此仍保留 `fit_03` 为基线。
上述结果来自随包报告，本次附包没有重新辨识或运行真机试验。

主要字段包括附加惯量、被动黏性损失、干摩擦、编码器偏置、等效 Kp/Kd、
等效力矩限幅、命令延迟和惯性张量倍率。每套的 `hand.json` 保存关节顺序和辨识环境；
向量必须按关节名称映射，不能直接当作 SDK J0–J20 顺序使用。
[bundle_info.json](pace_20261102/bundle_info.json) 提供 PACE 与 SDK 索引对应关系及单位。

## 与当前 URDF 的关系

当前 [`urdf/revo3_right.urdf`](../urdf/revo3_right.urdf) 的拇指 CMR 已按要求调整：

| 配置 | CMR 下限 / 上限（rad） | 总行程（rad） |
| --- | --- | --- |
| 辨识包记录 | 约 `-0.4224 / 1.4277` | 约 `1.8501` |
| 当前 URDF | `0 / 1.8501` | `1.8501` |

辨识包的 `hand.json` 和冻结参数继续保留辨识时的值，用于追溯原结果；
关节零位和旋转轴未因这次限位区间移动而修改。
原辨识资产是 `revo3_right_compact_v4.usda`，对应文件清单见
[asset_integrity.json](pace_20261102/asset_integrity.json)，本包不包含该资产或原始采集日志。
该资产与当前 URDF 重新生成的 USD 不是同一发布文件，当前 URDF 保留原始质量和惯性。
本次检查不证明参数迁移到当前资产后的动态响应等价。

此目录作为参数附件提供，没有将等效增益、摩擦、附加惯量或力矩限幅自动写进 URDF。
运行时应显式选择模型，保留其控制公式、按名称映射，并检查所用资产、限位和时间尺度。
新 CMR 区间的动态表现未在这次附包过程中重新验证。

## 校验与读取

从仓库根目录执行（Python 标准库，不启动 GPU）：

```bash
(cd revo3_system/parameters && sha256sum -c SHA256SUMS)
python3 revo3_system/parameters/pace_20261102/scripts/load_parameters.py
python3 revo3_system/parameters/pace_20261102/scripts/load_parameters.py --model balanced
```

加载器检查包内 23 份文件的校验值、冻结参数哈希、21 关节顺序及参数数值。
`checksums.json` 自身不包含在其校验列表内；ZIP 的外部校验值另存于 `SHA256SUMS`。
读取 API、完整回放依赖和控制公式见原始使用说明。
仿真显式 PD 周期为 5 ms，每周期两个物理子步；保存的延迟约 12.984 ms，
在该时间网格上有效为 3 个 PD 步（15 ms）。

`electrical/linear.json` 和 `electrical/clipped.json` 是独立的电流域拟合，
不能直接作为 Newton 力矩域参数或厂家 SDK 增益。
保留的 `runtime.lock.json`、`evidence/` 和 `figures/` 用于追溯原辨识与验证环境。
