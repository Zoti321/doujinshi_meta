# 凭证与代理

> 对应 ticket：[代理与哔咔凭证本地管理方案](../.wayfinder/tickets/007-grilling-credentials-proxy.md)

## 哔咔账号：环境变量

**禁止**将账号写入仓库或配置文件。运行时从环境变量读取：

| 变量 | 必填 | 说明 |
|------|------|------|
| `DTG_BIKA_EMAIL` | 哔咔命令时 ✅ | 登录邮箱 |
| `DTG_BIKA_PASSWORD` | 哔咔命令时 ✅ | 登录密码 |

流程：读取变量 → `POST /auth/sign-in` → token 内存持有（可选用户目录缓存）→ 401 重登。

禁漫 **不需要** 账号。

```bash
export DTG_BIKA_EMAIL="your@email.com"
export DTG_BIKA_PASSWORD="your-password"
uv run dtg fetch --source bika --ids abc123
```

---

## 代理：默认不使用

| 原则 | 说明 |
|------|------|
| **默认直连** | 未配置时代理为 `null`；**不**自动读取系统代理、`HTTP_PROXY` / `HTTPS_PROXY` |
| **手动启用** | 用户通过配置接口显式设置后才走代理 |
| **jmcomic** | 传入 `proxies=None`，覆盖库默认的 `system` 行为 |

### 不用代理时

| 场景 | 结果 |
|------|------|
| 禁漫（`api`） | 国内多数情况正常 |
| 哔咔（国内） | 常失败；需用户 **主动配置代理** 后重试 |
| 已开全局 VPN | 可能直连成功（视 VPN 路由） |

---

## 代理配置接口

用户 **手动设置** 后生效；支持三种方式，优先级 **高 → 低**：

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

- 哔咔连接失败且 `resolve_proxy()` 为 `None` 时，stderr 提示：可 `dtg config set proxy ...` 或 `--proxy`
- 日志永不打印密码；代理 URL 可打印（无敏感信息）

---

## 决策摘要

| 项 | 决定 |
|----|------|
| 默认 | **不使用代理**，直连 |
| 配置接口 | `dtg config set/unset/show` + `config.toml` + `--proxy` / `--no-proxy` + `DTG_PROXY` |
| 系统 `HTTPS_PROXY` | **不自动继承**（避免无意走代理） |
| 哔咔凭证 | `DTG_BIKA_EMAIL` / `DTG_BIKA_PASSWORD` |
