---
name: napcat-hub
description: 通过 NapCat 内置的 OneBot v11 HTTP API 操作 QQ 机器人——发私聊/群消息、查好友/群/群成员、调用任意 OneBot action。当用户提到 "NapCat"、"QQ 机器人"、"发 QQ 消息"、"QQ 群列表"、"bot.bg6hlq.cn" 时触发。
version: 1.0.0
---

# NapCat Hub

用 HTTP 直接驱动 NapCat 里的 QQ 账号（OneBot v11 协议）。

## 连接信息

| 项 | 值 |
|---|---|
| **Base URL** | `$NAPCAT_BASE`，默认 `http://bot.bg6hlq.cn:3043`（源站 8.133.219.133，阿里云杭州） |
| **鉴权** | Header `Authorization: Bearer $NAPCAT_API_KEY` |
| **实现** | NapCat.Onebot 4.18.33 / OneBot v11，QQ `56469543`（はたて） |

## ⚠️ 三个必须先知道的坑

1. **3043 就是 OneBot HTTP server，不是 WebUI。** 它底层是 Express，token 不对时返回
   `403 {"message":"token verify failed!"}` —— 长得像 WebUI 登录页，极易误判。
2. **除 3043 外所有端口（3000/3001/5700/6099/8080…）从沙箱侧全部 502 不可达。** 只有 HTTP 这一条路。
3. **沙箱里别用裸 socket 探测这个域名。** 域名会命中设备 TUN 的 fake-ip（`198.18.0.243`），
   `connect()` 秒成功、端口全报 OPEN，全是假的；`curl` 走 env proxy 的结果才真实。
   脚本用 `urllib`（自动读 `http_proxy`/`https_proxy`），所以是通的。

## 快速用法（脚本）

```bash
S=/var/minis/skills/napcat-hub/scripts/napcat.py

python3 $S me                     # QQ 56469543 (はたて)
python3 $S status                 # online=True good=True
python3 $S version                # NapCat.Onebot protocol=v11 version=4.18.33
python3 $S groups                 # 群列表（简表）
python3 $S friends                # 好友列表（37）
python3 $S members 879031937      # 群成员（标出 role / is_robot）
python3 $S group-info 1064668340
python3 $S stranger 2268551433

# 发消息（正文用 `-` 从 stdin 读，避免 shell 引号坑）
echo "测试" | python3 $S send-group 1064668340 -
python3 $S send-private 2268551433 "在吗"
python3 $S send-group 1064668340 "开会了" --at 2268551433 --at 56469543

# 任意 action（等价于 call）
python3 $S call get_group_honor_info '{"group_id":879031937,"type":"all"}'
python3 $S get_group_list          # 裸 action 名也可以
```

`--raw` 打印完整 JSON；`--base URL` 临时换服务器。

## 常用 OneBot action 速查

| 分类 | action | 参数 |
|---|---|---|
| 账号 | `get_login_info` / `get_status` / `get_version_info` | — |
| 好友 | `get_friend_list` / `get_stranger_info` | `user_id` |
| 群 | `get_group_list` / `get_group_info` / `get_group_member_list` / `get_group_member_info` | `group_id`, `no_cache` |
| 发消息 | `send_private_msg` / `send_group_msg` / `send_msg` | `user_id` 或 `group_id`, `message` |
| 消息操作 | `get_msg` / `delete_msg` / `mark_msg_as_read` / `get_forward_msg` | `message_id` |
| 群管理 | `set_group_ban` / `set_group_kick` / `set_group_whole_ban` / `set_group_card` | `group_id`, `user_id`, `duration`… |
| 请求处理 | `set_friend_add_request` / `set_group_add_request` | `flag`, `approve` |
| 媒体 | `get_image` / `get_record` / `can_send_image` / `can_send_record` | `file` |
| 系统 | `get_cookies` / `get_csrf_token` / `get_credentials` / `set_restart` | 域名等 |

全部 action 前缀 `POST http://bot.bg6hlq.cn:3043/<action>`，body 为 JSON。

## 消息段（CQ 码）

`message` 字段直接写 CQ 码即可：

```
[CQ:at,qq=2268551433] 你好          # @某人
[CQ:image,file=https://.../a.png]   # 发图（URL 或 file:// 本地路径）
[CQ:face,id=178]                     # 表情
[CQ:reply,id=12345] 收到             # 回复
```

## 发消息前的自检

- 发群消息前先 `groups` 确认 group_id（别硬编码）。
- 往陌生群/人发消息前先跟用户确认目标，避免误发。
- `status` 里 `online=false` 说明 QQ 掉线，先让用户去 NapCat 侧重新登录。

## 事件上报（收消息）

纯 HTTP 只能**主动调**，收不到消息。要监听事件需在 NapCat 侧二选一：

- **WebSocket 服务端**（NapCat 监听，本端连上去）：`ws://bot.bg6hlq.cn:<port>`，连上后推 `post_type=message` 等事件。
- **HTTP 上报/Webhook**（NapCat 往本端推）：需要本端有公网可达的 URL，沙箱内不现实。
- **反向 WS**：本端起 WS 服务端，NapCat 作为客户端连过来 —— 同样需要公网入口。

所以：沙箱里做「主动发/查」没问题；做「被动响应」得用户先把 WS 端口开出来。
