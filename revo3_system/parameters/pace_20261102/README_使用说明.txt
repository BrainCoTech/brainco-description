Revo3 PACE 已辨识参数与使用说明
打包日期：2026-11-02（Asia/Shanghai）
代码仓库：https://github.com/tannjieee/REVO3_PACE
匹配提交：936c813d45fca85a18ce366b6640cf1f1dceb005

一、先选择模型

models/fit_03/     原全关节冻结基线，默认加载此模型。
models/balanced/   最新七参数修正候选，尚未替代基线。

两套都包含完整 21 关节参数，不需要把 balanced 叠加到 fit_03。
原始 best_parameters.json 保持字节一致，selection_frozen.json 保存原选择哈希。
每套 hand.json 记录运行资产路径、关节顺序、姿态、重力、限位和仿真设置。
右手拇指 CMR 运行范围统一为 0～105°。
参数总览.html 可直接用浏览器打开，查看逐关节参数、SDK 索引和结果图表。
model_differences.json 精确列出七处变化，保留全部数值精度。

基线训练 RMSE：2.603° → 0.919°；4 Hz 阶段：3.803° → 1.163°。
七参数候选训练 RMSE 为 0.954°；目标瞬态 RMSE：
  拇指 CMP：6.519° → 5.419°；CMR：4.021° → 2.693°；
  无名指 PIP：3.992° → 1.700°。
共同时间窗下，全手 4 Hz RMSE 从 1.1637° 增至 1.3520°，
拇指 4 Hz 从 1.6048° 增至 2.3032°。因此候选不是全指标更优。
原留出阶跃已用于后续诊断与修正，尚无新的独立验证。

二、先校验、再读取（不需要 SDK、GPU 或 NumPy）

解压后在包目录运行 Python 3.12：
  python3 scripts/load_parameters.py
  python3 scripts/load_parameters.py --model balanced

脚本校验 checksums.json 中全部文件及模型原始冻结哈希；修改任何受校验
文件都会报错。checksums.json 用于发现文件变化，不是签名或身份认证。

在自己的 Python 程序中：
  import sys
  sys.path.insert(0, "/absolute/path/to/Revo3_PACE_parameters_20261102/scripts")
  from load_parameters import load_model
  parameters, hand = load_model("fit_03")
  names = hand["joint_names"]
  kp = parameters["effective_kp_Nm_rad"]
  kd = parameters["effective_kd_Nm_s_rad"]

使用绝对解压路径。参数表显示的是四舍五入值，程序应读取原 JSON。

三、字段含义与应用

armature_kg_m2           每关节附加惯量，kg·m²，叠加到资产动力学上。
viscous_Nm_s_rad         被动黏性损失，N·m·s/rad；与控制器 Kd 分开。
friction_Nm             Newton/MJWarp 干摩擦损失，N·m；不是接触摩擦系数。
encoder_bias_rad        q_encoder = q_geometry - bias，单位 rad。
effective_kp_Nm_rad     等效位置增益，N·m/rad。
effective_kd_Nm_s_rad   等效速度增益，N·m·s/rad。
effective_effort_limit_Nm  每关节模型力矩限幅，N·m；不是电流保护阈值。
delay_s                 共用命令延迟；原始值 0.012983980784281389 秒。
finger_body_inertia_scale  手指连杆完整惯性张量倍率，本次两套均为 1.0。

前七项均为长度 21 的向量，严格按照 hand.json 的 joint_names 排列。
不能把向量直接按 SDK J0–J20 顺序发送。bundle_info.json 的 joint_mapping
给出了从 0 开始的 PACE 索引与 SDK 索引；该命名映射不代替实物零位标定。
质量保持资产值（缺省 finger_body_mass_scale=1.0），固定手掌与重力保持
hand.json 所示设置；拇指 CMP 偏置固定 +1°，不是实测零位校准。
并非保存的所有字段都经过独立辨识；训练/固定/弱方向见 evidence 中审计。

hand.json 内 kp_Nm_rad / kd_Nm_s_rad 是后端回退值，不能替代
best_parameters.json 内已经辨识的 effective_kp / effective_kd。
必须把整个 parameters 传给 NewtonRollout.run，后端才会同时应用惯量、
摩擦、偏置、等效增益和等效限幅。不要将本包直接覆盖 configs/parameters.json，
后者是 nominal/bounds 配置，结构不同。

实际使用的控制形式（命令延迟模式）：
  q_encoder = q_geometry - bias
  d = floor(delay_s / dt + 0.5)
  tau[k] = clip(Kp*(q_target[k-d] - q_encoder[k])
                + Kd*(qd_target[k-d] - qd[k]), -limit, +limit)
  初始 q_geometry = 实测 q_encoder + bias；使用实测初速度。
  k-d < 0 时保持第一条命令。位置与速度目标均延迟、均采用零阶保持。

四、三个不同的时间尺度

仿真显式 PD 周期 5 ms；每周期两个物理子步，即 2.5 ms。
共用延迟量化为 3 个 PD 步，即有效 15 ms，不能称为 12.984 ms 的设备测量。
主机目标更新周期独立于 PD 和物理子步。30/25/20 Hz 的周期分别为
33.333…/40/50 ms，仅做过离线目标时序对照，未完成对应频率真机复测。
30 Hz 必须保留理想 1/30 秒时钟，在下一 PD 网格点因果生效，不能取整为 35 ms。
不能直接增大 hand.dt_s 来模拟主机降频，否则也改变了模型 PD 与延迟离散化。
固件内部控制周期尚未核验，不能将 5 ms 仿真网格解释为真机闭环周期。

五、运行一个实测阶段的仿真回放

需要匹配的 Isaac Lab / Newton GPU 环境（版本见 runtime.lock.json）、
具有使用权限的原机器人资产，以及完整 GUI MIT 实测原始目录。
本包不包含 USD、SDK、原始采集数据或完整训练实验。

安装工程的具体步骤见仓库 docs/SETUP.md。将资产放到项目
assets/revo3_right_compact_v4；asset_integrity.json 可用于核验相同资产。
先激活已安装的 Isaac Lab 环境，再进入工程目录，替换以下绝对路径：

  bash scripts/run.sh /absolute/path/to/Revo3_PACE_parameters_20261102/scripts/replay_example.py \
    --model fit_03 --raw /absolute/path/to/complete-recording \
    --stage thumb_constant_4Hz --out /absolute/path/to/new-output --prepare-only

通过输入检查后，移除 --prepare-only 执行 GPU 回放；--model balanced
可切换候选。完整日志目录需要 report.json、events.jsonl、raw_pace_order.npz，
加载器会校验源哈希、21 关节顺序、完成状态和时间轴。

脚本使用完整手、自碰撞检查及既有速度/求解诊断。输出目录必须不存在；
输出 prediction.npz 和 report.json，不拟合新参数、不连接实体手。
--prepare-only 只检查模型和输入，不启动 GPU、不产生预测文件。
本包仅包含加载和回放入口，不能直接传给既有训练脚本的 --parent / --fit：
那些入口还依赖完整历史 manifest、原始日志、父实验及保存的回放输出。

六、电流域增益：单独使用

electrical/linear.json  为线性电流响应拟合；clipped.json 为带限幅拟合。
每份含 21 关节系数、条件区间、训练/留出指标、源哈希及模型公式。
kp_A_per_rad、kd_A_s_per_rad、current_bias_A 的单位为 A/rad、A·s/rad、A。
clipped 的 effective_symmetric_current_saturation_A 是拟合饱和值，
不代表厂家保护电流，也不能用来更改硬件保护。
两种拟合有各自 effective_delay_s，不要拿它覆盖动力学模型的 delay_s。
带限幅模型是在查看线性模型留出结果后比较的，不属于全新盲测。
未标定电流到力矩的转换，电流域参数不由 Newton 优化器使用。
原报告保留原始来源路径用于追溯；加载模型不依赖这些历史路径。

七、适用条件与已有验证

针对固定掌部的 Revo3 Ultra21 右手、此次资产/固件条件下的自由空间响应；
采集 SDK 版本 2.3.2、固件 0.1.5，SDK Kp=3.0、Kd=0.1。
采集覆盖全关节、0.1–4 Hz 扫频、多频与阶跃。模型参数是等效值，
不能直接写入厂家 SDK Kp/Kd，也不证明物理参数唯一性、接触抓取或新设备适用性。

配套代码提交通过 98 项测试（两项 SDK 相关测试跳过）；2048 环境、208 个
冻结回放工况通过；重构前后最大预测差异小于 1e-6 rad。1914 个历史候选
评分完全一致，详见 evidence/refactor_regression.json。
这些是已有代码/模型验证，本次打包不代表新辨识或新真机试验。
checksums.json 覆盖所有交付内容（校验清单本身除外）。压缩包外的
SHA256 文件用于下载后核验压缩包本身。
