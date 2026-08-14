## Research Brief

- **Baseline**：用户仅给出样板用途（三份虚构周报：①缺陷检测结果 ②缺陷指标回收 ③缺陷相关项目进展）。无已有事实材料；样板中的公司数字、lot、工具编号将全部为演示用虚构数据，外部文献数字不得写成某家晶圆厂的真实成绩。
- **Declared gaps**：①浸没式光刻常见缺陷机制与中英行业名称；②检测周报常用指标及读法（D0、capture rate、nuisance、adder、killer/kill ratio、SEM review / non-visual）；③指标回收动作杠杆（水质量、淋洗/干燥、topcoat、浸没头/hood PM、扫描机污染、检测 recipe 阈值）——只列机制与行业实践；④项目进展周报通常跟踪的工作包。
- **Audience / intent**：晶圆厂光刻/缺陷工程周会（检测、良率、工艺、设备）；为样板提供行业事实词汇与机制基线，不做版式、页清单或设计决策。
- **Requested outcome**：事实补充 + 可进入样板的外部主张出处；输出语言 zh-CN。

**Material conflicts**：无。用户未提供可与外部文献冲突的公司实测数据。

**Usage note**：下文定量数字均为文献/路线图/专利中的机制或规格描述，不是任何量产厂的周报 KPI。样板中的 D0、lot、工具编号应继续使用虚构演示值。

---

## Gap 1：浸没式光刻常见缺陷机制与行业通用名称

193 nm 浸没式光刻（193i / ArF immersion）在最后透镜与晶圆之间维持超纯水弯月面（water meniscus）。ASML 指出，高速台运动下的水塘引入两类量产缺陷源：透镜下气泡会劣化成像；逃逸水滴会与光刻胶不可控地相互作用。控制手段是环绕末镜的 **浸没头 / immersion hood**，用以约束水塘。ASML 称该机构经工业化后，可在提高扫描速度的同时把缺陷率降低一个数量级；NXT:2050i 产品页仍将“新 immersion hood 减少失水、改善缺陷”列为量产卖点。

IMEC 在 ASML XT:1250Di 上与 ASML、TEL、KLA-Tencor、抗蚀剂供应商及 IC 制造商联合研究，将浸没特有缺陷模式归纳为：**空气气泡（air bubbles）**、**水印 / 水痕（watermarks / water marks）**、**晶圆边缘膜剥离（wafer edge film peeling）**、**颗粒输运（particle transport）**，并配套表征 **抗蚀剂溶出（resist leaching）** 与 **吸水（water uptake）**。SPIE Newsroom 综述进一步把几乎所有 193i 晶圆上可见的主要类型归为气泡、反气泡（anti-bubble）、水印、颗粒、微桥（microbridge），并称气泡与水印为浸没特有；反气泡、颗粒、微桥在干法中也可出现，但浸没增加额外来源。

| 中文（周报可用） | 英文行业术语 | 机制要点（文献） |
|---|---|---|
| 气泡缺陷 | bubble defect / air bubble | 附着于抗蚀剂表面的气泡起微透镜作用：中心欠曝、图案被放大、边缘出现剂量条纹；自由漂浮气泡离焦且寿命短，威胁主要来自贴附气泡。大直径（文献示例 >2 μm）较易辨认；约 100 nm 气泡可仅表现为小桥。来源：未优化曝光头夹带、供水气泡、抗蚀剂放气、表面夹带。 |
| 反气泡 / 透明颗粒微透镜 | anti-bubble defect | 透明顶层涂膜（topcoat）颗粒或鼓包折射率约 1.55（高于水），会聚曝光光：中心过曝、边缘因大入射角反射形成欠曝环、线距缩小。来源：topcoat 溶液久置析出、涂布碗壁干膜再吸、针孔吸水鼓包（blister）。干法亦可出现，浸没增加来源。 |
| 水印 / 水痕 | watermark / water mark (W/M) | 扫描后残留水滴改变局部抗蚀剂感度：PAG 等溶入水滴、水渗入膜；若带入 PEB，高温加速反应。SEM：圆形轮廓、中心线变粗甚至桥连，**线距不变**（无透镜放大）；截面可见表面 T-top。与气泡的鉴别点是“有无 pitch 放大/条纹”。 |
| 颗粒 / 团簇 | particle / cluster | 浸没水中颗粒或溶质干燥析出；弯月面从 **晶圆台（wafer stage）** 与 **晶圆边缘** 拾取松散碎片并输运到曝光区，还可交叉污染下一片。文献示例：1 mL 水中 2 ppt Fe 干燥后可形成约 100–200 nm 量级颗粒。 |
| 边缘膜剥离 / 掉膜 | wafer edge film peeling / flake | 浸没头扫过 EBR 区时流体力破坏膜边；抗蚀剂/topcoat 对裸 Si 附着力差、BARC 切边错位时易起片。氧化物、氮化物、low-k 等弱附着力膜同样可剥离。 |
| 溶出 / 浸出 | leaching（PAG、quencher 等） | 光酸发生剂、淬灭剂等小分子溶入浸没水，污染水、末镜与晶圆台，并改变抗蚀剂表面去保护，可导致 T-top 或桥连。快过程数秒内饱和（与镜头污染相关）；慢过程可达数分钟至约 20 分钟（与水印相关）。 |
| 吸水 / 溶胀 | water uptake / swelling | 水经针孔穿透 topcoat 到达抗蚀剂界面，使膜溶胀成圆形鼓包。 |
| 微桥 | microbridge | 相邻线被通常 <500 nm 的桥连接。干法已有（BARC、不透明颗粒挡光）；浸没额外来源包括小气泡挡光、水中颗粒局部欠曝、抗蚀剂–topcoat **互混层（intermixing layer）**。 |
| 团状 / 卫星斑 | blob defect / satellite spot defect | 多见于低图形密度区，直径文献范围约 10–50 μm；多为显影/淋洗时 topcoat 再沉积。机制与显影不均匀、DI 水淋洗导致的 pH 突变有关。 |
| 残渣 | residue | 文献中常与显影再沉积、干燥污斑（drying stain）、未洗净溶出物并称；不是单一独立机制名，周报宜与 blob / watermark / particle 交叉分类，避免单独当作浸没特有模式。 |

**鉴别口诀（来自成像机制，非厂内阈值）**：气泡改变 **pitch 并带条纹**；水印 **pitch 不变、表面 T-top**；反气泡有 **欠曝环 + 中心会聚**。

**未解析**：未检索到 SEMI 对上述中文译名的强制标准词表；上表为文献通用英文名 + 中文工程惯用并列。`residue` 无单独权威定义。

---

## Gap 2：缺陷检测周报常用指标与读法

以下指标回答“这一周检测结果是否可信、是否该动工艺/设备”，**不绑定任何厂的数值**。

### D0 / 缺陷密度（defect density）

IEEE 良率综述：最常用模型把良率与平均缺陷密度和管芯面积联系起来。泊松模型 \(Y=\exp(-D_0 A)\)，其中 \(D_0\) 为平均缺陷密度（缺陷/cm²），\(A\) 为管芯面积。该模型假定缺陷独立均匀分布；实际缺陷常在设备颗粒、工艺异常或边缘效应处聚集，泊松往往偏悲观，负二项模型引入聚集参数。IEEE IRDS Yield Enhancement 将缺陷预算分配到各工艺模块，并用每层缺陷密度（有时以每 300 mm 晶圆缺陷数 \(D_x\) 表述）对接产品良率。

**周报通常回答**：本周随机缺陷负荷相对基线是升还是降？是否超出模块缺陷预算？空间图是全片系统性问题还是边缘/扫描路径相关？

### Capture rate（捕获率）

ITRS Yield Enhancement（2003）将“对关键缺陷类型的高捕获率检测”列为持续挑战，并把 **killer defect 的检测概率** 称为 capture rate。IEEE *Transactions on Semiconductor Manufacturing* 论文将 inline 检测的 killing-defect detection probability 与 capture rate 等同，并提出用良率冲击/kill ratio 与理论临界面积关系、或用“干净管芯良率 vs 已解释良率冲击”来估计未检出杀伤缺陷的份额。KLA 配方专利把 DOI capture、nuisance rate、稳定性作为配方候选的评价统计量。

**周报通常回答**：当前 recipe 是否抓得到本周关注的 DOI（缺陷类型/尺寸）？捕获率掉了是真缺陷变少，还是灵敏度/照明模式漂移？

### Nuisance（干扰缺陷）vs false（假点）

ITRS 明确区分：

- **Nuisance**：工具报了事件，晶圆上确有物理现象，但 **不是当前关注类型**（DOI）；日后仍可能有研究价值。
- **False**：工具报了事件，但用检测工具自身的 review 光学路径 **看不见任何缺陷**；用于验证配方。

KLA（经 Nikon Precision 转载）补充：nuisance 来自真实物理（如 dummy 图形上的颗粒、孤立区颗粒、线边粗糙度被 die-to-die 算法当成缺陷），不影响器件性能/良率；系统毛刺才是 false。高灵敏度（hot）扫描会抬高 nuisance。ITRS 路线图表述：图形晶圆 nuisance 在各阶段宜低于 5%；false 在研发 <5%，在良率爬坡与量产 <1%。这是路线图目标，不是某厂实测。

**周报通常回答**：总数上升是 DOI 恶化，还是 nuisance/假点污染了 Pareto？要不要收阈值或改光学模式？

### Adder（新增缺陷）

KLA 杀伤比分析把 **clean die** 定义为“没有被检出的 adder 缺陷（如颗粒）”，**dirty die** 为含 adder。ITRS 把 near-zero **defect adder** 数据的统计处理列为难题。浸没场景的设备级对应实验是 **PWP（particles per wafer pass，每片通过颗粒数）**：预检极干净的空白片走浸没 track/scanner（不曝光图形），再检，判断浸没头是否向晶圆添加缺陷图案；多次 PWP 平均以提高信噪比。

**周报通常回答**：本站点/本步骤 **新引入** 了什么（相对前层或进站）？扫描机/浸没头本周 PWP 是否漂移？不要把前层或来料缺陷当成当周浸没 adder。

### Killer / kill ratio（杀伤缺陷 / 杀伤比）

Kill ratio 是“某类缺陷导致管芯失效的估计比例”，由历史生产数据中 **inline 缺陷位置与终测 bin 图对准** 得到。KLA 杀伤比术语：用含 DOI 的 dirty die 良率相对干净管芯良率估计该类缺陷的杀伤力；再按尺寸、位置等属性分箱，在 kill ratio 突变处设阈值，定义 yield-impacting DOI。总缺陷数往往与终测良率相关性差；按杀伤 DOI 计数做 SPC 更合理。ITRS 亦将 fault-to-defect mapping 与 kill ratios 列为良率学习挑战。

**周报通常回答**：本周 Pareto 最高柱是不是真杀伤类型？该不该按 kill ratio 而不是按颗数排优先级？

### SEM review 与 SEM non-visual（SNV / non-visual）

光学检测产出缺陷坐标（如 KLARF），再抽样送 SEM 复核分类。Applied Materials / GLOBALFOUNDRIES 工作指出：传统配方常把 nuisance 压到约 10% 以便数据量可管理，但节点缩小后会牺牲 DOI 灵敏度；改为“先保灵敏度、接受更高 nuisance”，则 SEM 复核方法必须跟上。KLA Process Watch：Pareto 最高柱经常是 **SNV（SEM Non-Visual）**，有的厂直接标 **Not Found**。更准确是 “Not Found Again”：光学已检出，SEM 再定位时看不见。四类原因：

1. 检测系统毛刺/噪声导致的 **false event**（现代工具较少）；
2. 检测与 SEM 坐标系不准，缺陷落在 SEM 视场外；
3. **前层缺陷**：对光学波长透明、对电子束不透明的膜下缺陷，**理应** 为 SEM non-visual；
4. **Nuisance variation**（如 LER）：die-to-die 算法报出，单张 SEM 图像不易辨认。

IEEE TSM（IBM/KLA）提出：光刻层 non-visual 率可作为“含光刻在内的前段膜质量”指示，而不应一律忽略。前层可用 **DSA（defect source analysis）** 与前层结果对位。高 SNV 会掩盖真正 DOI，延误良率学习。

**周报通常回答**：SEM 抽样后的分类 Pareto 是否代表整片？SNV 高是坐标/视场问题、前层、还是 recipe 过热？该增加 SEM 抽样还是先降 nuisance 捕获？

### 检测 recipe 阈值在周报中的位置

配方包含光学（波长、孔径、偏振）、机械与算法阈值/分段。KLA：用这些旋钮压低 nuisance 捕获、保住 DOI。提高灵敏度会同时抬高 nuisance 与后续 SNV。周报应同时看 **DOI 捕获、nuisance 比例、SNV 比例、稳定性**，避免只报总数。

**未解析**：未找到 SEMI 规定“周报必须列出的指标清单”或 D0 的统一工厂算法（含不含边缘、是否归一化到扫描面积）。各厂实现会差；样板应把指标当词汇/读法，数值保持虚构。

---

## Gap 3：指标回收的动作杠杆（机制与行业实践）

只列机制与文献中的实践方向。**不把未证实的回收百分比写成周报目标。** 个别文献给出的实验范围仅用于说明“效果高度依赖材料/机台”，不是承诺值。

### 浸没水质量（UPW）

标准洁净室 DI 水电阻率 >18.2 MΩ·cm **仍需再抛光** 才能进扫描机。SPIE 专著描述的处理链：过滤（去除 >30 nm 颗粒）、控温、脱气、UV 杀菌。溶解氧从室温饱和约 10 ppm 降到 <70 ppb；有机物从 ppb 降到 ppt，否则在镜头上形成 haze 并吸收 193 nm 光。出水示例规格：电阻率 >18 MΩ·cm，阴阳离子元素污染约 10–30 ppt 量级，TOC <50 ppt；水温目标 20.5 °C、精度 <0.01 °C；管路需定期消毒。ASML 专利（US7733459B2 及后续）给出浸没液可声称的规格窗口示例：电导率约 0.055–0.5 μS/cm，有机物 ≤5 ppb（优选 ≤1 ppb），≥50 nm 颗粒 ≤2 个/mL（优选 ≤0.5 个/mL），溶解氧 ≤15 ppb（优选 ≤5 ppb），硅 ≤500 ppt（优选 ≤100 ppt）。这些是设备/流体规格，不是某厂周报实绩。

**杠杆**：点检 UPW 电阻率/TOC/颗粒/溶解氧/硅；确认脱气与终端过滤；检查细菌与有机物回升（haze、干燥颗粒）。

### 淋洗 / 干燥（pre-rinse / post-rinse）

浸没 track 相对干法可增加：曝光前 DI 淋洗（冲掉易溶出组分）、曝光后 DI 淋洗（尽快去掉残留水滴以减水印）、以及 topcoat 相关步骤。预淋洗后溶出水平在文献中可降到未淋洗的约 12%，时间常数约降一半；对比曲线显示 10–30 s 预淋洗对抗蚀剂感度影响很小，因为曝光头在曝光前有约 1–2 s 的“固有冲洗”。后淋洗对水印的效果 **强烈依赖抗蚀剂叠层**：SPIE Newsroom 报道有的材料缺陷数可明显下降，有的几乎无效，并归因于吸水，当时仍在研究。若水滴停留过久，后淋洗无效。

**杠杆**：检查 pre/post-rinse 是否启用、延迟时间、干燥是否在 PEB 前完成；不要用单一百分比承诺回收幅度。

### Topcoat / 无顶层涂膜抗蚀剂

Topcoat 作为阻挡层抑制溶出与吸水。三条工艺路径：溶剂可溶 topcoat、显影液可溶 topcoat、无 topcoat。量产主流曾是 **显影液可溶 topcoat**（TMAH 同模块去除）。光学上 topcoat 折射率宜约 1.55 以匹配水（1.44）与典型 193 nm 抗蚀剂（约 1.7）；推荐厚度多在 30–90 nm。溶解速率高有助于减少 blob（文献范围约 100–1000 nm/s）。疏水（高后退接触角）有利于减水滴，但与 blob（疏水膜在水系显影中溶解慢）存在权衡。溶剂可溶 topcoat 可做到后退角 >100°，文献演示缺陷密度可降至 0.1/cm² 量级——这是材料组合演示，不是某厂量产成绩。无 topcoat 可减少涂布缺陷源与成本，但需同时满足低溶出与成像；早期样品工艺窗口可小于优化过的抗蚀剂/topcoat 基线。Nikon 等评估过 TC-less 在高速扫描下对 topcoat blister 类缺陷的抑制，以及疏水表面对弯月面稳定的帮助；blob 仍是疏水表面的显影淋洗课题。

**杠杆**：核对抗蚀剂–topcoat 兼容性（互混、膜损、LER、工艺窗口）、PAB/PEB 与 topcoat 烘烤匹配、溶液过滤与涂布碗清洁、疏水 vs blob 权衡。

### 浸没头 / hood PM 与扫描速度

弯月面后退失稳（film pulling、meniscus overflow）会留下残液。后退接触角（receding contact angle, RCA）与拖尾水滴强相关；RCA→0° 时留下水膜。全扫描速度下，文献广泛采用 **RCA 约 70°** 作为避免拖尾水滴的经验门槛；缺陷数随 RCA 在临界角附近非线性下降。扫描速度升高时动态 RCA 下降、前进角上升。曝光路径与扫描速度需与 hood 设计匹配。ASML 将 hood 视为控制水塘的核心硬件；后续机型继续用新 hood 减失水。气泡抑制：优化曝光头、完全脱气、低放气抗蚀剂。

**杠杆**：hood/末镜 PM、气帘/气隙与水流设定、扫描速度与 RCA 是否仍匹配、气泡相关空间签名是否沿扫描路径。

### 扫描机污染（台面、镜头、交叉污染）

弯月面从晶圆台拾取前片留下的颗粒/干斑。长期生产后台面必然积累颗粒与干渍，**例行清洁晶圆台** 可降低交叉污染。溶出组分会污染末镜（flare、透过率下降）与设施。文献实践包括：浸没系统 **in-situ cleaning**（清洗溶剂随浸没水流过、或向水中通 CO₂ 等）、PWP 在清洗前后对比、Nikon/TEL 联合的机上周期淋洗与边缘淋洗/切边位置控制。TEL：弱附着 topcoat 与边缘残渣可用 pre-rinse 去掉；切边位置过浅会使水更频繁冲击切线而剥膜。HMDS 附着促进：较低温度、较长处理有利于附着（Nikon 等剥膜实验）。

**杠杆**：PWP 趋势、台面/hood 清洁周期、末镜 haze/透过率、边缘切线与 EBR/WEE、进片边缘/bevel 颗粒。

### 检测 recipe 阈值

回收“检测结果”不一定等于工艺变好：收紧阈值或改光学模式可降低 nuisance/SNV 捕获，也会牺牲 DOI 捕获。KLA 建议：若已排除前层，可将 nuisance variation 单独分箱，或改孔径/波段/偏振以降低对此类 SNV 的捕获。周报应把“recipe 变更”与“工艺/设备变更”分列，避免把灵敏度调整误读为缺陷工程回收。

### 边缘与附着

EBR 去除松散边珠，使边缘能抵抗弯月面；WEE 可整形膜边。最佳 EBR 依赖材料，需实验。附着力不足时 BARC 对集成膜堆也可能剥离。

**未解析**：ASML/Canon/Nikon 公布过动态溶出速率规格表，但本次未能从专著插表中可靠抄出具体 ng/cm²/s 数值；仅能确认规格随 hood/水流而异，Nikon 曾因“水从镜头流向抗蚀剂、污染在镜头下游”将早期规格放宽约 15 倍。不要在样板中填写未核验的溶出规格数字。

---

## Gap 4：浸没缺陷相关项目进展周报通常跟踪的工作包

未检索到 SEMI/IEEE 规定的“浸没缺陷项目周报 WBS 标准模板”。下列工作包是从权威工程文献中反复出现的闭环归纳，可供样板做栏目，而非强制清单。

1. **工艺窗口与叠层兼容（process window / resist–topcoat stack）**  
   抗蚀剂与 topcoat 组合的曝光宽容度、LER、剖面、膜损；PAB/topcoat PAB/PEB 的 DOE；扫描速度 vs RCA；有/无 topcoat 路线；互混层与微桥。目标是窗口不因浸没叠层而塌缩。

2. **设备清洁与浸没头/台面健康（tool cleanliness / hood PM）**  
   周期 in-situ cleaning、机上淋洗、晶圆台清洁、涂布碗清洁、末镜有机污染与颗粒；PWP 作为工具健康代理指标；意外污染后的液体清洗路径（经 immersion nozzle 引入）。Nikon/TEL：边缘淋洗、切边位置、进片异物控制以保护曝光机。

3. **检测灵敏度与监测策略（inspection sensitivity）**  
   图形片 vs 非图形片（如 Surfscan）相关性；DUV 波长以抓住可见光漏检的小缺陷；ADI/光刻单元监控；DSA 区分当层 vs 前层；SEM 复核与 SNV 治理；配方在 DOI 捕获与 nuisance 之间的再平衡。Nikon 量产缺陷论文强调：特征缩小要求更高灵敏度，并需确认非图形监控与图形缺陷的相关。

4. **物料 / 化学品（materials & chemicals）**  
   UPW 规格与 TOC/颗粒/硅/溶氧；抗蚀剂溶出测试与 QCM 吸水；topcoat 过滤与货架析出；HMDS/EBR 溶剂；低溶出或 TC-less 抗蚀剂导入；显影/表面活性剂淋洗对 blob 与倒塌的影响。IBM 等强调水–抗蚀剂界面同时约束扫描速率（film pulling）与 PAG 抽出。

5. **边缘工程（wafer-edge / EBR / WEE）**  
   常从“设备清洁”独立成包：浸没头对 EBR 区的力学损伤、bevel 颗粒回运、切线粗糙度与切边高度。IMEC/IntechOpen 综述：干法 EBR 已知，浸没使边缘与水、台面形成双向输运。

6. **长期稳定性与量产资格（HVM stability）**  
   长时间缺陷稳定性、cluster 可用性、意外污染后的恢复程序。这是项目进展（而非单周检测快报）的典型收口项。

**系统化拆因方法（可写入项目进展“方法”栏）**：以稳定干法为基线，在 topcoat 涂布、PAB、浸没曝光、topcoat 去除、显影等 **每个新增步骤后做检测 + SEM 复核**，用步骤间差分定位来源。

**未解析**：没有公开的“周报必须包含的里程碑字段”（如百分比完成率、owner RACI）。样板可用上述工作包做栏目，进度数字保持虚构。

---

## Sources

1. https://doi.org/10.1117/12.660432
2. https://www.asml.com/en/news/stories/2023/how-immersion-lithography-saved-moores-law
3. https://www.asml.com/en/products/duv-lithography-systems/twinscan-nxt2050i
4. https://www.asml.com/en/news/press-releases/2006/asml-presents-leading-edge-immersion-results
5. https://web.archive.org/web/20230719195354/https://spie.org/news/0976-non-lensing-defects-and-defect-reduction-for-193i
6. https://web.archive.org/web/20230719195354/https://spie.org/news/0975-bubble-and-antibubble-defects-in-193i-lithography
7. https://web.archive.org/web/20230719195352/https://spie.org/news/0758-immersion2-mastering-the-resist-leaching-and-aqueous-contact-angle-challenges
8. https://web.archive.org/web/20230719195355/https://spie.org/news/0825-immersion-lithography-topcoat-and-resist-processes
9. https://doi.org/10.1117/3.820233
10. https://lab.semi.ac.cn/library/upload/files/2022/2/15135949239.pdf
11. https://doi.org/10.1116/1.2090968
12. https://doi.org/10.1117/12.711058
13. https://doi.org/10.1117/12.655517
14. https://doi.org/10.1117/12.660158
15. https://doi.org/10.1117/12.657179
16. https://doi.org/10.1117/12.711464
17. https://doi.org/10.1117/12.658413
18. https://doi.org/10.1117/12.814238
19. https://doi.org/10.1117/12.814112
20. https://doi.org/10.1117/12.712400
21. https://doi.org/10.1117/12.846520
22. https://doi.org/10.1117/12.881479
23. https://doi.org/10.1117/12.2523963
24. https://patents.google.com/patent/US7733459B2/en
25. https://technav.ieee.org/topic/integrated-circuit-yield/
26. https://irds.ieee.org/images/files/pdf/2024/2024IRDS%5FYE.pdf
27. https://www.semiconductors.org/wp-content/uploads/2018/08/YieldEnhanc2003.pdf
28. https://sst.semiconductor-digest.com/2012/05/process-watch-the-dangerous-disappearing-defect/
29. https://www.nikonprecision.com/newsletter/fall_2009/article_04.html
30. https://www.kla.com/products/chip-manufacturing/defect-inspection-review
31. https://doi.org/10.1109/tsm.2013.2273294
32. https://doi.org/10.1109/tsm.2005.852122
33. https://patents.google.com/patent/US20140072203A1/en
34. https://www.freepatentsonline.com/9714905.html
35. https://www.buildings.com/home/article/55259243/improve-led-manufacturing-via-in-line-monitoring-and-spc-magazine
36. https://www.intechopen.com/chapters/8660
37. https://research.ibm.com/publications/fluoroalcohol-materials-with-tailored-interfacial-properties-for-immersion-lithography
38. https://doi.org/10.1117/12.712095
39. https://iopscience.iop.org/article/10.1088/1361-6501/aafd77
