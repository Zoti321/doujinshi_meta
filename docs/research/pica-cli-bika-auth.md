# pica-cli 哔咔认证与代理调研

> 调研日期：2026-08-30  
> 来源：[justorez/pica-cli](https://github.com/justorez/pica-cli)（TypeScript CLI，哔咔漫画下载器）  
> 对照项目：[`docs/credentials.md`](../credentials.md)、[`src/doujinshi_tag_getter/sources/bika.py`](../../src/doujinshi_tag_getter/sources/bika.py)

---

## 1. 结论摘要

| 问题 | 结论 |
|------|------|
| 代理是否**代码层面必填**？ | **否**。未设置 `PICA_PROXY` 时客户端直连 API（`proxy: false`）。 |
| 代理是否**所有环境都能直连**？ | **否**。取决于运行环境能否访问 `picaapi.picacomic.com`；GitHub Action 在海外 runner 上可免代理。 |
| 用户侧凭证是否只需账号+密码？ | **是**（用户秘密）。`PICA_ACCOUNT` + `PICA_PASSWORD`，或交互式输入。 |
| 客户端是否还需其他常量？ | **是**（非用户秘密）。`api-key`、`secret_key`、App 模拟头硬编码于客户端；`PICA_SECRET_KEY` 可覆盖默认值。 |
| Token 是否用户配置？ | **否**。`POST /auth/sign-in` 返回后内存持有。 |

---

## 2. 代理：可选，非强制

### 2.1 源码行为

构造函数仅在环境变量存在时启用代理，否则 `proxy: false`（直连）：

```35:48:https://github.com/justorez/pica-cli/blob/main/src/sdk.ts
    constructor() {
        const httpProxy = process.env.PICA_PROXY
            ? new URL(process.env.PICA_PROXY as string)
            : false
        this.api = axios.create({
            baseURL: 'https://picaapi.picacomic.com/',
            proxy: httpProxy
                ? {
                      protocol: httpProxy.protocol,
                      host: httpProxy.hostname,
                      port: Number(httpProxy.port)
                  }
                : false
        })
```

`.env.template` 中 `PICA_PROXY=` 为空，注释为「代理地址，示例：http://127.0.0.1:7890」——**非必填项**。

### 2.2 GitHub Action：无代理、仅账号密码

工作流 secrets 只注入 `PICA_ACCOUNT` 与 `PICA_PASSWORD`，**未设置** `PICA_PROXY`：

```48:58:https://github.com/justorez/pica-cli/blob/main/.github/workflows/task.yml
env:
  PICA_IN_GITHUB: true
  PICA_ACCOUNT: ${{ secrets.PICA_ACCOUNT }}
  PICA_PASSWORD: ${{ secrets.PICA_PASSWORD }}
  PICA_DL_CONTENT: ${{ inputs.PICA_DL_CONTENT }}
  ...
```

README 明确：GitHub Action 方式「**不用科学上网**，网速飞快」——代理需求被**运行环境**替代，而非客户端强制。

### 2.3 与「国内直连常失败」的关系

| 层面 | pica-cli | 本项目 [`docs/credentials.md`](../credentials.md) |
|------|----------|--------------------------------------------------|
| 客户端设计 | 代理可选 | 代理可选（默认 `null` 直连） |
| 网络现实 | 本地国内常需代理；海外 runner 不需要 | 文档写「哔咔（国内）常失败」 |
| 语义 | 「不刚需代理」= 软件不强制配置 | 与 pica-cli 一致；「刚需」指特定网络环境 |

**精确定义**：代理不是 API 调用的**逻辑前提**，而是**可达性**问题——能直连 `picaapi.picacomic.com` 的环境无需代理。

---

## 3. 凭证：用户只需账号与密码

### 3.1 登录流程

```110:125:https://github.com/justorez/pica-cli/blob/main/src/sdk.ts
    async login(account: string, password: string) {
        const res = await this.request<string>('post', 'auth/sign-in', {
            email: account,
            password: password
        }).catch((err) => {
            throw new Error('登录失败，请检查账号/密码/网络环境')
        })
        if (!res.token) {
            throw new Error('PICA_SECRET_KEY 错误')
        }
        this.token = res.token
    }
```

入口 [`src/index.ts`](https://github.com/justorez/pica-cli/blob/main/src/index.ts)：`PICA_ACCOUNT` / `PICA_PASSWORD` 缺失时交互式询问，无 token 预填。

### 3.2 用户秘密 vs 客户端常量

| 类型 | pica-cli | 本项目 |
|------|----------|--------|
| **用户秘密** | `PICA_ACCOUNT`（邮箱）、`PICA_PASSWORD` | `DTG_BIKA_EMAIL`、`DTG_BIKA_PASSWORD` |
| **客户端常量**（硬编码） | `api-key`、`headers.json` 中 App 头 | `bika.py` 中 `API_KEY`、`DEFAULT_HEADERS` |
| **签名密钥** | `PICA_SECRET_KEY` 环境变量，有代码内 fallback | `SECRET_KEY` 硬编码于 `bika.py` |
| **会话 token** | 登录后内存 | 登录后内存，401 重登 |

固定请求头见 [`src/data/headers.json`](https://github.com/justorez/pica-cli/blob/main/src/data/headers.json)（含 `api-key: C69BAF41DA5ABD1FFEDC6D2FEA56B` 等），与社区逆向一致。

### 3.3 签名算法（与 pica_crawler 同源）

pica-cli 作者注明参考 [pica_crawler](https://github.com/lx1169732264/pica_crawler)。签名拼接：

```
raw = url + timestamp + nonce + method + api-key  →  lower()  →  HMAC-SHA256(secret_key)
```

与 [`bika.py`](../../src/doujinshi_tag_getter/sources/bika.py) 中 `_sign()` 一致；**用户无需提供**签名参数。

---

## 4. 与本项目 `bika.py` 的细微差异

| 维度 | pica-cli | 本项目 |
|------|----------|--------|
| nonce | `headers.json` **固定**值 | **每请求随机** `secrets.token_hex(16)`（更合理，保留） |
| app-channel | `2` | `"1"` |
| app-build-version | `45` | `"44"` |
| 401 重登 | 无 | 有（加分项，保留） |
| 签名公式 / api-key / secret | 一致 | 一致 |

图片下载路径（HTTPS→HTTP、手动重定向）本项目不需要（只爬 tag 元数据）。

---

## 5. 对本项目的含义

1. **凭证模型已对齐**：环境变量邮箱+密码 → `POST /auth/sign-in` → token，与 pica-cli 相同。
2. **「不刚需代理」应写清两层**：
   - 产品/代码：默认直连，代理为可选增强；
   - 运维/环境：国内本地用户可能仍需手动配代理或依赖 VPN/海外机器。
3. **不必让用户配置 token / api-key / secret_key**；若 `secret_key` 过期，应更新客户端常量（或支持 `DTG_BIKA_SECRET_KEY` 类覆盖，类似 pica-cli 的 `PICA_SECRET_KEY`）。
4. **GitHub Action 模式**对本 tag 爬虫项目通常不适用（需长期本地/CI 枚举）；但说明「代理非 API 契约要求」仍有参考价值。
5. **无需为对齐 pica-cli 而改 nonce/channel**；仅在签名/兼容失败时再试 `app-channel=2`、`app-build-version=45`。

---

## 6. 参考链接

- [justorez/pica-cli](https://github.com/justorez/pica-cli)
- [pica-cli src/sdk.ts](https://github.com/justorez/pica-cli/blob/main/src/sdk.ts)
- [pica-cli readme.md](https://github.com/justorez/pica-cli/blob/main/readme.md)
- [pica-cli .env.template](https://github.com/justorez/pica-cli/blob/main/.env.template)
- [pica-cli task.yml](https://github.com/justorez/pica-cli/blob/main/.github/workflows/task.yml)
- 本项目：[docs/credentials.md](../credentials.md)、[docs/research/bika-api-tags.md](./bika-api-tags.md)
