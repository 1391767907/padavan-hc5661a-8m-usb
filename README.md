# Padavan 云编译 · HC5661A（MT7628NN 8M+64M · GPIO38 · USB网卡）

针对你的板子实测参数定制：

| 项目 | 值 |
|------|-----|
| 机型名 | **HC5661A** |
| SoC | MT7628NN / MT7628A |
| Flash | **8MB**（W25Q64） |
| RAM | **64MB** |
| 复位键 | **GPIO38** |
| USB | 开启；补丁让 `usb0`(RNDIS) 走 NDIS WAN，可当 4G WAN |
| Storage 分区 | `0x20000`（128KB，避免 8M 上 Storage 越界） |

源码：`hanwckf/rt-n56u`（kernel 3.4）

---

## 一键云编译（GitHub Actions）

1. 把本目录 `padavan-cloud` 推到你的 GitHub 仓库（新建空仓库后上传全部文件）
2. 打开仓库 → **Actions** → **Build HC5661A Padavan (8M+64M USB)** → **Run workflow**
3. 等编译结束（约 1～2 小时）→ **Artifacts** 下载 `padavan-HC5661A-8M-USB`
4. 用刷机工具 / TFTP / 网页升级刷入 `.trx`（或包内固件）

> 本机未装 `git`/`gh` 时：用 GitHub 网页 “Upload files”，或安装 [Git for Windows](https://git-scm.com/download/win) 后再推送。

### 用 Git 推送示例

```bash
cd padavan-cloud
git init
git add .
git commit -m "HC5661A 8M USB padavan cloud build"
git branch -M main
git remote add origin https://github.com/<你的用户名>/<仓库名>.git
git push -u origin main
```

---

## 目录说明

```
padavan-cloud/
├── boards/HC5661A/
│   ├── board.h              # GPIO38 复位等硬件定义
│   ├── board.mk             # USB口=1
│   └── kernel-3.4.x.config  # 8M Storage + USB网卡驱动
├── templates/HC5661A.config # 精简插件（适配8M）+ 开USB
├── scripts/prepare.sh       # 把定制文件覆盖进源码
└── .github/workflows/
    └── build-hc5661a.yml    # 云编译工作流
```

---

## 刷机注意

1. 先备份当前配置；8M 空间紧，本配置已关掉 Aria/Samba/Transmission 等大件  
2. 刷完后 Storage 应正常（不再是 size=0）  
3. USB 网卡/中兴 RNDIS：插入后应出现 `usb0`，在「USB网卡/4G模块」里启用  
4. 若刷机变砖：串口 115200，U-Boot 用 TFTP 救砖  

---

## 相对原厂 HC5661A 模板的改动

- `CONFIG_FIRMWARE_ENABLE_USB=y` + `BOARD_NUM_USB_PORTS=1`
- 内核启用 `rndis_host` / `cdc_ether` / `ax8817x` 等
- `CONFIG_MTD_STORE_PART_SIZ=0x20000` 适配 8MB Flash
- 大幅精简用户态插件，避免固件撑爆 8M
