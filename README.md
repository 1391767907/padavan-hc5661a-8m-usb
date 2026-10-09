# HC5661A Padavan 定稿

MT7628NN · 8MB Flash（W25Q64）· 64MB RAM · 复位 GPIO38 · USB 4G RNDIS WAN。

## 出厂默认

| 项目 | 值 |
|------|-----|
| 后台地址 | http://192.168.123.1 |
| 账号 | `admin` |
| 密码 | `admin` |
| WiFi 名称（2.4G） | `HC5661A_` + MAC 后缀 |
| WiFi 密码 | `1234567890` |
| DHCP | `192.168.123.100` – `192.168.123.244` |
| 串口 | **115200** 8N1 |

## 定稿参数

| 项目 | 定稿 |
|------|------|
| 机型 | HC5661A |
| 源码 | hanwckf/rt-n56u（kernel 3.4） |
| 固件 | `firmware/HC5661A_3.4.3.9-099.trx` |
| 云编译 | https://github.com/1391767907/padavan-hc5661a-8m-usb |

## 源码

```
boards/HC5661A/     硬件、8M Storage、USB/RNDIS 内核配置
templates/          精简模板，USB=y
patches/            usb0 作为 NDIS WAN（上游只认 weth/wwan）
scripts/prepare.sh  覆盖板级文件并打补丁
.github/workflows/  GitHub Actions 云编译
```

出厂默认：`modem_rule=1`、`modem_type=3`（NDIS），插入 USB 4G 网卡后自动把 `usb0` 当 WAN。

## 刷机

网页 / TFTP / breed 刷入 `firmware/HC5661A_3.4.3.9-099.trx`。

- 刷完若仍是旧网段 / 旧 WAN，清 NVRAM 或恢复出厂后再用
- 变砖：U-Boot TFTP 救砖

重新编译：仓库 Actions → **Build HC5661A Padavan (8M+64M USB)** → Run workflow，只取产物里的 `.trx`。
