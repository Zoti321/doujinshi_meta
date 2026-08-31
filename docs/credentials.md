# 凭证与代理

> 对应 ticket：[代理与哔咔凭证本地管理方案](../.wayfinder/tickets/007-grilling-credentials-proxy.md)  
> 调研依据：[pica-cli 哔咔认证与代理调研](./research/pica-cli-bika-auth.md)

## 哔咔：用户凭证

**禁止**将账号写入仓库或配置文件。解析顺序：

1. 环境变量 `DTG_BIKA_EMAIL` / `DTG_BIKA_PASSWORD`（两者均非空则直接使用）
2. 否则在交互终端提示手动输入（密码优先 `getpass` 掩码；**Git Bash / mintty 下 `getpass` 无法读键，自动改用可见输入并警告**）
3. 非交互且无 env（如管道 EOF）→ 报错退出

| 变量 | 说明 |
|------|------|
| `DTG_BIKA_EMAIL` | 登录邮箱（可选；缺失则提示输入） |
| `DTG_BIKA_PASSWORD` | 登录密码（可选；缺失则提示输入） |

用户 **只需** 提供上述两项。`api-key`、HMAC 签名密钥、App 模拟头等 **客户端常量** 由代码内置，无需用户配置（参见 [`CONTEXT.md`](../CONTEXT.md)）。

流程：解析凭证 → `POST /auth/sign-in` → token **内存持有** → 401 自动重登。

禁漫 **不需要** 账号。

```bash
# 方式 A：环境变量
export DTG_BIKA_EMAIL="your@email.com"
export DTG_BIKA_PASSWORD="your-password"
uv run dtg fetch --source bika --ids abc123

# 方式 B：直接运行，按提示输入
uv run dtg fetch --source bika --ids abc123
```

> **Token 缓存**：首版不持久化，每次进程启动重新 login；全量爬取阶段若需减少 login 频率，再考虑可选用户目录缓存。

---

## 代理：默认不使用（非 API 必填）

代理 **不是** 哔咔 API 调用的逻辑前提，而是 **网络可达性** 兜底：当运行环境无法直连 `picaapi.picacomic.com` 时，用户手动启用。

| 原则 | 说明 |
|------|------|
| **默认直连** | 未配置时代理为 `null`；**不**自动读取系统代理、`HTTP_PROXY` / `HTTPS_PROXY` |
| **手动启用** | 用户通过配置接口显式设置后才走代理 |
| **jmcomic** | 传入 `proxies=None`，覆盖库默认的 `system` 行为 |

### 直连时的网络现实

| 场景 | 典型结果 |
|------|----------|
| 禁漫（`api`） | 国内多数情况正常 |
| 哔咔 + 国内本地 Windows | **可能**失败；失败时配置代理或开 VPN 后重试 |
| 哔咔 + 全局 VPN / 海外 runner | 常可直连成功 |
| 已配置 `--proxy` / `DTG_PROXY` | 走用户指定代理 |

### 失败提示规则

| 失败类型 | 条件 | 用户可见提示 |
|----------|------|--------------|
| **网络连接失败**（如无法连通 API、超时） | 当前为直连（未配置 proxy） | 错误信息含可操作建议：`dtg config set proxy ...` 或 `--proxy`（环境建议，非 API 必填） |
| **网络连接失败** | 已配置非空 proxy | 报告连接失败，**不再**主推「去设代理」 |
| **登录/鉴权失败**（错误密码、`code=200` 但缺 `data`/`token` 等） | 任意 | 聚焦账号/密码；若确认凭证无误，也可能是客户端 HMAC `secret_key` 错误；**不**把「去设代理」作为主建议 |

---

## 代理配置接口

用户 **手动设置** 后生效；优先级 **高 → 低**：

| 优先级 | 方式 | 示例 |
|--------|------|------|
| 1 | 单次 CLI | `dtg --proxy http://127.0.0.1:7890 fetch ...` |
| 2 | 单次禁用 | `dtg --no-proxy fetch ...`（忽略持久配置） |
| 3 | 持久配置文件 | 见下文 `config.toml` |
| 4 | 环境变量 | `export DTG_PROXY=http://127.0.0.1:7890` |

### 持久配置：`dtg config`

配置文件路径（自动创建目录）：

- Windows：`%APPDATA%\doujinshi-tag-getter\config.toml`
- Linux/macOS：`~/.config/doujinshi-tag-getter/config.toml`

```bash
# 查看当前配置
dtg config show

# 设置代理（持久）
dtg config set proxy http://127.0.0.1:7890

# 清除代理（恢复默认直连）
dtg config unset proxy

# 指定配置文件（可选）
dtg --config /path/to/config.toml catalog --source bika
```

`config.toml` 示例：

```toml
# 省略或注释掉 proxy = 直连（默认）
proxy = "http://127.0.0.1:7890"
```

### Python 库 API

```python
from doujinshi_tag_getter import fetch_tags
from doujinshi_tag_getter.config import load_config, resolve_proxy

cfg = load_config()                          # 读用户 config.toml
proxy = resolve_proxy(config=cfg)            # None = 直连

fetch_tags("jmcomic", ["410090"], proxy=proxy)
fetch_tags("bika", ["id1"], proxy="http://127.0.0.1:7890")  # 显式覆盖
```

| 参数 | 默认 | 说明 |
|------|------|------|
| `proxy` | `None` | `None` 直连；字符串为 HTTP(S) 代理 URL |
| `proxy` 显式传入 | 覆盖配置文件 | |

---

## 实现约定

```python
@dataclass
class UserConfig:
    proxy: str | None = None  # 默认 None

def resolve_proxy(
    *,
    cli_proxy: str | None = None,
    cli_no_proxy: bool = False,
    config: UserConfig | None = None,
) -> str | None:
    """返回 None 表示不使用代理（直连）。"""
    if cli_no_proxy:
        return None
    if cli_proxy is not None:
        return cli_proxy or None
    if config and config.proxy:
        return config.proxy
    return os.environ.get("DTG_PROXY") or None
```

- 日志永不打印密码；代理 URL 可打印（无敏感信息）

---

## 决策摘要

| 项 | 决定 |
|----|------|
| 用户凭证 | `DTG_BIKA_EMAIL` / `DTG_BIKA_PASSWORD`；缺失时交互提示输入 |
| 客户端常量 | 硬编码于 `bika.py`；密钥轮换时改代码或后续加 `DTG_BIKA_SECRET_KEY` 覆盖 |
| Token | 首版内存持有，401 重登；持久化缓存延后 |
| 代理 | **非 API 必填**；默认直连，手动启用 |
| 失败提示 | 直连+网络失败 → 提示配置代理；已设代理或登录/鉴权失败 → 不主推「去设代理」 |
| 配置接口 | `dtg config set/unset/show` + `config.toml` + `--proxy` / `--no-proxy` + `DTG_PROXY` |
| 系统 `HTTPS_PROXY` | **不自动继承**（避免无意走代理） |
| 主要运行环境 | 国内本地 Windows；失败时再配代理 |
