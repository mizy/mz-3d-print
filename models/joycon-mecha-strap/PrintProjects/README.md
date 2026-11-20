# Joy-Con 用户打印工程

`working.3mf` 是用户保存的 Bambu Studio 工程，2026-11-20 按要求原样复制入库。没有修改工程内容，没有执行切片。

## 保存时的状态
- Bambu Lab P1S，0.4 mm 喷嘴，0.2 mm 层高/首层。
- 一件灰色主体 `BODY_GRAY_TO_HEIGHT.stl`，两件白色 `BUTTON_PRINT_TWO.stl`。没有青色顶层部件。
- 主体已旋转，当前高度约 12.7 mm，不能套用侧放分层版的 14.6 mm 换色高度。
- 两墙、顶底各两层、15% 蜂窝，按对象打印，自动 brim。
- 保存时全局支撑关闭。原作者要求主体默认朝向带支撑；打印前需由用户检查悬空、按钮侧放及逐对象喷头避碰。此归档不表示设置已被修改或打印验证通过。

## 限制
本文件包含三角网格和用户打印配置，不是参数化 CAD/STEP。参考按钮无独立弹簧，原控制器配合、回弹、锁止与腕绳承载均未实测。此前仅做不含控制器的几何按压检查，不能据此保证实物适配或安全。

## 来源与许可
主体/按钮基础几何：Cool Kid，Fully 3d Printable Replacement Strap for Nintendo Switch Joy-Con，Printables 580201，发布于 2023-09-14，CC BY 4.0。原作者基于 youmu_i19 的 Nintendo Switch Joy-Con Strap。
https://www.printables.com/model/580201-fully-3d-printable-replacement-strap-for-nintendo-/files
https://creativecommons.org/licenses/by/4.0/

改动：原参考主体网格并集，添加原创机甲侧饰，按高度拆分装饰；用户自行设置摆放、颜色和打印配置。无原作者认可或任天堂认证。没有使用 MakerWorld 受限制参考的几何。

`archive.json` 记录原始文件名和 SHA-256，可验证此工程为原样复制。仓库里其他历史料盘改动不属于本次提交。
