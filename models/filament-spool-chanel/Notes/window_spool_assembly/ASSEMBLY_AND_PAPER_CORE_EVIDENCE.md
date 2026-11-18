# 最新42 mm长窗候选：装配与纸芯证据独立审查

对象SHA aebd14b1a16cb334717231dbe5325379227dd089aa0515e8a4cdc158a85b9dd5。本报告不修改源；实际最新STEP全体BRep路径由主实现者另行运行，不以旧模型结果冒充新运行。

## 装配坐标与已有独立证据

官方原STL正确右手局部化：wide=(sourceY,-sourceZ,33.7000007629-sourceX)，narrow=(sourceY,sourceZ,sourceX+33.7000007629)。盘外侧z=0，向锁口为+z。将narrow先Rx180再Rz(theta)，轴向平移H；不得将并排展示位置当装配，也不得对wide作镜像。

H=66.4 mm来源是wide外套止挡z40.7加narrow肩z25.7。官方源原摆放盘距67.4不代表落座。名义外套内R39与窄颈外R38.9在圆柱配合段径向差0.10 mm（直径差0.20），这是理想CAD尺寸，不含打印误差、椭圆化、纸芯力或弹性。

在H66.4时，narrow颈z25.7..27.9映到wide z40.7..38.5。wide窗顶35与该已知配合段下缘间隔3.5 mm；wide完整上环高5.7 mm。narrow窗顶22保留肩/颈前区域，但不能据此推断装配刚度不变。

既有官方原生基准离散BRep路径：theta51°，H72→66.4每0.2 mm；H66.4，theta51→9每2°及8°，交叠体积均0。H66.5、theta8有1.1330 mm³交叠，说明在轴向保留区。8°只是越止退凸点前无刚性交叠的保留区，不是官方“卡嗒锁好”已证明。H66.4 theta0有0.36855 mm³，theta3约4.20452；错误入口H70 theta45约2.497。

独立直接官方STL截面积积分（0.05 mm中点步长）证实相应刚性交叠源本来存在：H66.4 theta0=0.364201、theta3=4.196764、theta8=0；H70theta45=2.500324、theta48=.476036、theta50=0 mm³。theta3交叠位于4处止退凸点/宽片R29.9边。数字近似与基准CAD相符，不代表弹性越障、扭矩、疲劳安全得到验证。

原报告与脚本：Notes/official_parametric_validation/{OFFICIAL_STL_ASSEMBLY.md,official_assembly_overlap.json,official_assembly_overlap_extra.json,assembly_path.json}。

## 纸芯真实来源核对

用户Downloads官方STL和官方wiki附件只有wide、narrow及spacing_shim，未发现纸芯CAD、标注尺寸图或纸芯公差。项目记录也没有用户纸芯的实测ID/OD/宽度。不能把STL筒外径当纸芯内径，不能把间距垫片当纸芯宽度测量。未使用第三方论坛/模型的81或82 mm等数字作为标准。

重新通过普通HTTP读取官方安装页：https://wiki.bambulab.com/en/general/swaping-new-filament-with-bambu-reusable-spool
网页明确要求纸芯缺口对准wide定位键、窄半旋转至卡响，再按流程解除保护带；没有给出纸芯ID/OD/宽度/公差。官方可打印模型页 https://wiki.bambulab.com/zh/knowledge-sharing/bambu-reusable-spool 也没有纸芯尺寸，且明确打印件可靠性不等同原装并不建议用于烘干。
网页快照refill_install.html及去脚本文本refill_install.txt可复查。

已知主体配合包络：wide外径81.70、narrow81.30 mm，wide局部键外端R43.7须有相应纸芯缺口，底boss局部外形更大并随z变化。只有在实际纸芯内径D被测出后，才能计算主体名义径向差(D−81.7)/2与(D−81.3)/2；这些公式不包含底boss、键或变形，不是完整配合判定。

轴向可用宽度也不是直接H66.4：须扣除纸芯接触半径处的左右台阶/盘表面，并考虑纸芯缺口与卷料边缘。没有纸芯内外径及端面位置就不能给唯一轴向间隙或建立声称真实的纸芯实体。

## 开窗造成的可量化支承变化

由最终源42 mm切向窗宽、圆柱主体几何独立计算，在远离上下R3圆角的窗口中高截面：
- wide每窗删去外周约61.871°，剩余四柱总周向覆盖31.254%，每柱外周弧长约20.055 mm。
- narrow每窗删去约62.210°，剩余周向覆盖30.878%，每柱外周弧长约19.717 mm。
- 开窗轴向跨度wide30.5 mm、narrow17.5 mm；上下圆角及完整端环并不按此删去比例。
这是局部中高截面几何覆盖率，不是全筒面积损失或承载能力下降比例。证据paper_core_support_geometry.json。

保持内导管、桥、上部套合外形不能消除约69%中段圆周支承缺失带来的纸芯跨窗挠曲、椭圆化、松线陷入、孔边刮擦、支撑残留问题。需要实测纸芯ID/OD/长度/缺口及材料刚度，或实际试装与负载验证才能回答“这卷纸芯兼容”。本任务不猜这些数值，不创建假纸芯冒充已验证附件。

## 对外结论边界

可以报告实际最新STEP离散路径的干涉结果（待主实现者完成），可报告原官方也存在止退局部刚性交叠，以及配合面名义保留。不能说已完成真正最终卡止/卡响的弹性验证，更不能说未提供尺寸的纸芯已验通过。
