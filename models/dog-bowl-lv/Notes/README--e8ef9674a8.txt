离线切片诊断（非可打印文件）
Bambu Studio 02.09.01.70 CLI 对主碗和 Logo 均返回 Success 且生成 G-code，无网格错误或警告。
但直接加载系统 JSON 的继承参数未完整解析，实际输出 filament_density=0，耗材重量=0，不能视为有效打印配置或可靠耗材/时长估计。
尝试配置：A1 0.4 / 0.20mm Standard / Bambu PLA Basic；这是诊断假设，并非确认用户设备。
未将这些候选 G-code 放入交付目录，未启动打印。正式切片验收、AMS 映射及温度校验仍待完成。
