# Revo3 辨识参数

提供右手 21 关节的等效动力学与控制参数，包括附加惯量、黏性损失、干摩擦、
编码器偏置、Kp/Kd、力矩限幅和命令延迟。CMR 运行范围为 **0～106°**。
2026-11-07 按用户填写表同步全部 21 关节运行限位，其中 11 个关节范围有变化；辨识参数、编码器偏置与默认姿态保持不变。

| 模型 | 用途 | 参数 |
| --- | --- | --- |
| `fit_03` | 默认基线 | [best_parameters.json](pace_20261102/models/fit_03/best_parameters.json) |
| `balanced` | 部分瞬态响应优化候选 | [best_parameters.json](pace_20261102/models/balanced/best_parameters.json) |

每套均包含完整的 21 关节参数。向量顺序见各模型的 `hand.json`；
单位和 SDK 索引映射见 [bundle_info.json](pace_20261102/bundle_info.json)。
`balanced` 尚未替代默认基线。

## 使用

在仓库根目录运行：

```bash
python3 revo3_system/parameters/pace_20261102/scripts/load_parameters.py
python3 revo3_system/parameters/pace_20261102/scripts/load_parameters.py --model balanced
```

加载器使用 Python 标准库，自动检查文件完整性和关节顺序。
控制器应读取 `best_parameters.json` 中的 `effective_kp_Nm_rad`、
`effective_kd_Nm_s_rad` 等字段，并按关节名称配置。
显式 PD 周期为 **5 ms**，每周期两个物理子步，有效命令延迟为 **15 ms**。

- [下载参数包](Revo3_PACE_parameters_20261102.zip)
- [参数总览和图表](pace_20261102/参数总览.html)
- [完整使用说明](pace_20261102/README_使用说明.txt)
- [当前限位与零位保持检查](../validation/right_joint_limits_20261107.json)
- [原参数包验证记录（2026-11-02）](../validation/pace_bundle_20261102.json)

`electrical/` 中保存独立的电流域拟合结果；等效动力学参数用于仿真，
不直接对应厂家 SDK 的增益寄存器。
