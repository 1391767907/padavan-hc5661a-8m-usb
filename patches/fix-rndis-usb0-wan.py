#!/usr/bin/env python3
"""Make Padavan treat rndis_host usbN as NDIS WAN (ZTE/Android RNDIS).

Upstream only hotplugs weth*/wwan*; rndis_host creates usb0 and is ignored,
so WAN stays on eth2.2 while usb0 sits DOWN.
"""
from __future__ import annotations

import pathlib
import sys


def must_contain(path: pathlib.Path, needle: str) -> str:
    text = path.read_text(encoding="utf-8", errors="surrogateescape")
    if needle not in text:
        raise SystemExit(f"[patch] missing expected text in {path}: {needle!r}")
    return text


def patch_file(path: pathlib.Path, old: str, new: str, label: str) -> None:
    text = must_contain(path, old)
    if new.strip() in text and old not in text:
        print(f"[patch] already applied: {label}")
        return
    path.write_text(text.replace(old, new, 1), encoding="utf-8", errors="surrogateescape")
    print(f"[patch] applied: {label}")


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} /path/to/rt-n56u", file=sys.stderr)
        return 2
    root = pathlib.Path(sys.argv[1])
    trunk = root / "trunk"

    # 1) mdev: fire mdev_net for usb0 created by rndis_host
    init_c = trunk / "user/rc/init.c"
    patch_file(
        init_c,
        'fprintf(fp, "%s 0:0 0660 %s/sbin/%s $MDEV $ACTION\\n", "weth[0-9]",    "*", "mdev_net");\n'
        '\t\tfprintf(fp, "%s 0:0 0660 %s/sbin/%s $MDEV $ACTION\\n", "wwan[0-9]",    "*", "mdev_net");\n',
        'fprintf(fp, "%s 0:0 0660 %s/sbin/%s $MDEV $ACTION\\n", "weth[0-9]",    "*", "mdev_net");\n'
        '\t\tfprintf(fp, "%s 0:0 0660 %s/sbin/%s $MDEV $ACTION\\n", "wwan[0-9]",    "*", "mdev_net");\n'
        '\t\tfprintf(fp, "%s 0:0 0660 %s/sbin/%s $MDEV $ACTION\\n", "usb[0-9]",     "*", "mdev_net");\n',
        "init.c mdev usb[0-9]",
    )

    # 2) recognize usbN as usbnet iface
    netutils = trunk / "user/shared/netutils.c"
    patch_file(
        netutils,
        "int is_usbnet_interface(const char *ifname)\n"
        "{\n"
        '\tif(!strncmp(ifname, "weth", 4))\n'
        "\t\treturn 1;\n"
        '\tif(!strncmp(ifname, "wwan", 4))\n'
        "\t\treturn 1;\n"
        "\treturn 0;\n"
        "}\n",
        "int is_usbnet_interface(const char *ifname)\n"
        "{\n"
        '\tif(!strncmp(ifname, "weth", 4))\n'
        "\t\treturn 1;\n"
        '\tif(!strncmp(ifname, "wwan", 4))\n'
        "\t\treturn 1;\n"
        '\tif(!strncmp(ifname, "usb", 3))\n'
        "\t\treturn 1;\n"
        "\treturn 0;\n"
        "}\n",
        "netutils.c is_usbnet_interface usb*",
    )

    # 3) NDIS ifname discovery: prefer wwan/weth, then usb
    usb_modem = trunk / "user/rc/usb_modem.c"
    patch_file(
        usb_modem,
        "get_modem_ndis_ifname(char ndis_ifname[16], int *devnum_out)\n"
        "{\n"
        "\tint valid_node = 0;\n"
        "\n"
        '\tvalid_node = find_modem_node("wwan", 0, 0, -1, devnum_out); // first exist node\n'
        "\tif (valid_node >= 0) {\n"
        '\t\tsprintf(ndis_ifname, "wwan%d", valid_node);\n'
        "\t\treturn 1;\n"
        "\t} else {\n"
        '\t\tvalid_node = find_modem_node("weth", 0, 0, -1, devnum_out); // first exist node\n'
        "\t\tif (valid_node >= 0) {\n"
        '\t\t\tsprintf(ndis_ifname, "weth%d", valid_node);\n'
        "\t\t\treturn 1;\n"
        "\t\t}\n"
        "\t}\n"
        "\n"
        "\treturn 0;\n"
        "}\n",
        "get_modem_ndis_ifname(char ndis_ifname[16], int *devnum_out)\n"
        "{\n"
        "\tint valid_node = 0;\n"
        "\n"
        '\tvalid_node = find_modem_node("wwan", 0, 0, -1, devnum_out); // first exist node\n'
        "\tif (valid_node >= 0) {\n"
        '\t\tsprintf(ndis_ifname, "wwan%d", valid_node);\n'
        "\t\treturn 1;\n"
        "\t}\n"
        '\tvalid_node = find_modem_node("weth", 0, 0, -1, devnum_out); // first exist node\n'
        "\tif (valid_node >= 0) {\n"
        '\t\tsprintf(ndis_ifname, "weth%d", valid_node);\n'
        "\t\treturn 1;\n"
        "\t}\n"
        "\t/* rndis_host / cdc_ether typically register as usbN */\n"
        '\tvalid_node = find_modem_node("usb", 0, 0, -1, devnum_out);\n'
        "\tif (valid_node >= 0) {\n"
        '\t\tsprintf(ndis_ifname, "usb%d", valid_node);\n'
        "\t\treturn 1;\n"
        "\t}\n"
        "\n"
        "\treturn 0;\n"
        "}\n",
        "usb_modem.c get_modem_ndis_ifname usb*",
    )

    patch_file(
        usb_modem,
        '\t\tsnprintf(node_fname, sizeof(node_fname), "%s/weth%d", MODEM_NODE_DIR, i);\n'
        "\t\tunlink(node_fname);\n"
        "\t\t\n"
        '\t\tsnprintf(node_fname, sizeof(node_fname), "%s/wwan%d", MODEM_NODE_DIR, i);\n'
        "\t\tunlink(node_fname);\n"
        "\t}\n"
        "}\n",
        '\t\tsnprintf(node_fname, sizeof(node_fname), "%s/weth%d", MODEM_NODE_DIR, i);\n'
        "\t\tunlink(node_fname);\n"
        "\t\t\n"
        '\t\tsnprintf(node_fname, sizeof(node_fname), "%s/wwan%d", MODEM_NODE_DIR, i);\n'
        "\t\tunlink(node_fname);\n"
        "\t\t\n"
        '\t\tsnprintf(node_fname, sizeof(node_fname), "%s/usb%d", MODEM_NODE_DIR, i);\n'
        "\t\tunlink(node_fname);\n"
        "\t}\n"
        "}\n",
        "usb_modem.c unlink_modem_ndis usb*",
    )

    # 4) factory defaults: enable NDIS modem WAN (type=3)
    defaults = trunk / "user/shared/defaults.c"
    patch_file(
        defaults,
        '\t{ "modem_rule", "0" },\n'
        '\t{ "modem_prio", "1" },\n'
        '\t{ "modem_type", "0" },\n',
        '\t{ "modem_rule", "1" },\n'
        '\t{ "modem_prio", "1" },\n'
        '\t{ "modem_type", "3" },\n',
        "defaults.c modem NDIS enabled",
    )

    # 5) LAN / Web UI 192.168.123.1 (macros in defaults.h)
    defaults_h = trunk / "user/shared/defaults.h"
    patch_file(
        defaults_h,
        '#define DEF_LAN_ADDR		"192.168.2.1"\n'
        '#define DEF_LAN_DHCP_BEG	"192.168.2.100"\n'
        '#define DEF_LAN_DHCP_END	"192.168.2.244"\n',
        '#define DEF_LAN_ADDR		"192.168.123.1"\n'
        '#define DEF_LAN_DHCP_BEG	"192.168.123.100"\n'
        '#define DEF_LAN_DHCP_END	"192.168.123.244"\n',
        "defaults.h LAN 192.168.123.1",
    )

    print("[patch] rndis usb0 WAN support done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
