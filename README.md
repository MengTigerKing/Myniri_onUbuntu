# Myniri_onUbuntu

个人 Ubuntu 24.04 x86_64 桌面迁移包：Niri 26.04、Clavis、Quickshell 0.3.1、Qt 6.10.3、Kitty 0.49.2。
保存当前源码修改、配置、字体、Reversal 图标、壁纸和已编译运行组件。部署不需要 Docker，也不升级 Ubuntu。

## 新电脑部署

也可以直接复制 `artifacts/Myniri_onUbuntu-ubuntu24.04-x86_64-full.tar.gz` 和同名
`.sha256` 文件到新机器。这是包含源码、配置及运行包的完整压缩包，不需要再克隆仓库或下载运行附件：

```bash
sha256sum -c Myniri_onUbuntu-ubuntu24.04-x86_64-full.tar.gz.sha256
tar -xzf Myniri_onUbuntu-ubuntu24.04-x86_64-full.tar.gz
cd Myniri_onUbuntu
python3 scripts/deploy.py
python3 scripts/deploy.py --apply --install-deps --system
```

若使用 GitHub 仓库与独立运行附件，则按下面步骤部署。

适用 Ubuntu **24.04 桌面版、Intel/AMD 64 位**。ARM、其他 Ubuntu 版本不适用此二进制包。
需要网络安装 Ubuntu 软件源依赖及管理员权限；保留原有 Ubuntu/GNOME 登录入口。

1. 克隆本仓库，进入仓库目录。
2. 把配套的 `ubuntu24.04-x86_64-runtime.tar.gz` 放进 `artifacts/`。
   本机目录已经包含该文件；从 GitHub 克隆后需要另行下载对应 Release 附件。
3. 先检查，再部署：

```bash
python3 scripts/deploy.py
python3 scripts/deploy.py --apply --install-deps --system
```

使用普通用户运行，不要在整条命令前加 sudo。脚本只在安装软件包和系统会话文件时调用 sudo。
默认检查命令只读，验证 Ubuntu 版本、CPU 架构、压缩包 SHA-256 和缺失依赖。
部署命令安装依赖、Niri 登录入口、用户文件和服务，下次登录启用 Clavis。
保存工作后注销，在登录页面齿轮菜单选择 **Niri**，然后登录。

## 保留的体验

- Win+T：Kitty；Win+E：文件管理器；Win+Z：应用搜索。
- Win+Shift+S：选区截图；Win+O：全局预览；Win+Alt+L：Clavis 锁屏。
- Win+Shift+Left/Right：上一张/下一张壁纸；Win+A/D：向左/右切换应用。
- Win+Shift+F：真正全屏，保留 Kitty 等应用自身的背景透明与模糊；不强制降低普通应用的不透明度。
- 壁纸取色、主题色文件图标、窗口圆角、透明模糊、壁纸毛玻璃锁屏。
- 隐藏底部 Dock、禁用左上角热区、Fcitx5 中文输入、终端虚字提示与光标动画。
- 蓝牙配对确认代理随 Niri 启动，提供 PIN 输入和配对码确认，复用 Clavis 通知。

蓝牙代理使用 Ubuntu 软件源的 Blueman 组件，Niri 中不启动其完整托盘。
新机安装依赖时会安装 Blueman；当前导出机器使用用户目录中的官方包组件。
蓝牙配对记录和设备密码不迁移，鼠标、耳机需要在新机器重新配对。
Ubuntu 运行包的 Quickshell 使用 glibc；用户服务通过 `60-memory.conf` 将分配器 arena 上限设为 4，减少多线程内存碎片。
媒体暂停或停止时暂停进度定时器，继续通过播放器事件同步切歌和跳转；播放时保持原来的 250ms 刷新。
以上优化不降低分辨率、刷新率、透明、模糊、动画或侧栏预加载。
锁屏和账户卡的发行版图标使用包内的 `Symbols Nerd Font Mono`，避免普通文字字体的私用码位冲突。
VS Code 集成终端可将 `terminal.integrated.fontFamily` 设置为 `"'JetBrains Mono', 'Symbols Nerd Font Mono', monospace"`；部署不覆盖整份 VS Code 设置。
显示布局计算已统一分数缩放时的像素取整，避免拖动贴边后出现一像素重叠。
分辨率增大或缩放减小时，仍需在布局图中移动显示器，避免真正的区域重叠。
未迁移当前机器的显示器专属位置和分辨率，也不启用其 outputs.kdl；新机器登录后自行设置。

Niri 包含本地透明全屏补丁（`manifests/niri.patch`），移除了全屏时遮挡背景的黑色底层。
透明度由应用自身控制；没有启用透明背景的应用仍不透明，Niri 的全局窗口 opacity 规则在全屏时仍沿用上游行为。
源码快照已经包含补丁，不要重复应用。运行包中的 Niri 同步重新编译，替换后需要注销并重新登录。
当前机器通过用户级 niri.service 覆盖加载新版，保留系统原版作为回退；新机由部署程序直接安装新版系统二进制。

新用户家目录在部署时自动填入，壁纸放入 `~/Pictures/Wallpapers`。
覆盖前备份保存至 `~/.local/share/myniri-backups/时间/`，包括被替换的用户文件和系统文件。
脚本不会重启桌面、删除 GNOME/Snap/Docker、改 ROS、设置自动登录或迁移密码。
旧的 niri-waybar、niri-mako、niri-background、niri-idle 用户服务停止自启动，
由 Clavis 接管界面和空闲策略；当前会话不被停止。
图标取色会更新用户的 GNOME icon-theme 设置，因此切回 GNOME 可能沿用图标主题。

## 目录和 GitHub 保存方式

| 目录 | 内容 |
| --- | --- |
| sources/ | Clavis、key-cli、Quickshell、Niri、Xwayland Satellite 独立源码快照及原许可证 |
| home/ | 用户配置模板和启动脚本；@HOME@ 由部署程序替换 |
| manifests/ | 上游版本、当前源码差异、APT 依赖和运行包哈希 |
| scripts/ | 本机导出工具和迁移部署工具 |
| artifacts/ | 约 395 MiB 的运行包及校验文件；已排除在 Git 之外 |

**只推送 Git 文件并不能完整恢复桌面，必须同时保存运行压缩包。**
GitHub 普通 Git 不接受这个大小的单文件。可以将运行包作为私有仓库 Release 附件保存，
保持 manifests/runtime.json 与附件配套；本次只整理本地文件，没有提交、推送或创建 Release。
无需保存 Docker 镜像、旧 /apps/deps 构建缓存、整个 Qt SDK 或用户历史记录。

更新源码、配置或运行包后，可执行 `python3 scripts/bundle.py` 重新生成完整压缩包和
SHA-256 校验文件。脚本先校验运行包，再打包部署所需目录；不会递归包含完整包自身、
Git 历史或 Python 缓存。完整包同样位于被 Git 忽略的 `artifacts/`，可单独备份或作为 Release 附件。

没有打包账号密码、SSH/GPG 密钥、浏览器资料、钥匙串、剪贴板、输入法个人词库和旧清理备份。
新机首次使用需要自行设置钥匙串及相关 API 凭据。锁屏使用新机器的 Linux 用户密码。
运行包含个人壁纸；对外公开前请确认图片及字体的分发许可，见 [THIRD_PARTY.md](THIRD_PARTY.md)。

## 验证与限制

光标使用 Breeze，默认逻辑尺寸 48。用户主题补齐高分屏图片尺寸，保留原图、动画和热点，
并通过 `~/.icons/breeze_cursors` 兼容旧版 libXcursor 的搜索路径。Clavis 同步 GTK 与用户服务
启动环境中的光标设置。已运行的应用可能需要重新打开才能更新光标缓存。
`scripts/expand-cursor-theme.py` 可从系统 Breeze 重建图片（需要 Pillow）；大尺寸由位图插值生成。

已在当前 Ubuntu 24.04 上验证归档校验、临时目录解压和路径替换、Niri 配置、
迁移后的 Quickshell/Kitty 版本命令、运行库解析，以及 APT 安装模拟。
另已验证临时家目录中的 key/sysmon 命令、配置覆盖备份和原生 QML 模块加载。
透明全屏补丁通过 release 编译、当前 Niri 配置校验及嵌套合成器截图检查：
原版的透明/模糊终端全屏后变黑，新版保留背景，完全不透明的终端仍保持不透明。
无显示模块检查产生 2 项预期警告（offscreen 与 Wayland 环境、Qt.quit 无接收者），
检查进程由超时结束；日志在导出机器的 /tmp/myniri-import-check.log。
Shell 脚本通过语法检查；当前环境没有 ShellCheck，未执行该项静态检查。
尚未在全新 Ubuntu 虚拟机完成图形登录、解锁、输入法和休眠的端到端验证。
显卡驱动、显示缩放、键盘设备权限和 API 凭据需要按新机器实际情况配置。
CPU 能耗等权限相关指标可能不可用；脚本不会自动授予读取键盘设备权限。
可选的 MapLibre、ddcutil、rclone 等组件不保证可用，未将当前机器已有警告描述为全部修复。

需要预览全部落盘内容而不安装时：

```bash
python3 scripts/deploy.py --stage /tmp/myniri-preview
```

源码项目仍彼此独立；本迁移包不会将 key-cli 合并到 Clavis。
未来改 QML/主题可直接编辑源码；修改 C++/Qt 后需重新构建对应组件并重新导出运行包。
本包提供已编译迁移路径，未提供从空白系统一键重编全部依赖的保证。
