# 使用 Nuitka 构建 Windows Standalone 二进制

集成宿主（尤其 Flutter 桌面）无法假定用户已安装 Python，需分发 **Standalone 二进制**。在 PyInstaller 与 Nuitka 之间选择 **Nuitka**：编译型产物启动更快、体积相对可控，且 v1 仅目标 **Windows x64**，可接受 MSVC 构建链前置条件。PyInstaller onefile 构建简单但冷启动与体积劣势明显，留作未选方案。默认 **onefile**（`djm.exe` 单文件便于打进宿主 assets）；调试缺模块时用 **`--onedir`**。配置与凭证仍写用户目录（`%APPDATA%\doujinshi-meta\`），不因 frozen 而改变语义。
