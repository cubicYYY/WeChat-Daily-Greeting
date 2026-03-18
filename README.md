# WeChat 

每日问候机器人 —— 通过微信公众号模板消息，每天定时发送天气、空气质量和自定义留言。
你可以 Fork 并进行自定义。

## 功能

- 可配置城市的实时天气（Open-Meteo，无需 API Key）
- 美国 EPA 标准空气质量指数 (AQI)
- 当地时间（美东）和北京时间
- 自定义一次性留言（发送后自动消耗）+ 默认留言兜底

## 消息模板示例

```
当地时间：2026-03-17 08:00:00
北京时间：2026-03-17 21:00:00

今日天气：
   - 杭州：多云 12°C （最高16°C 最低8°C）
   - 西拉法叶：晴 5°C （最高12°C 最低-1°C）

空气质量：
   - 杭州：AQI 68 （良）
   - 西拉法叶：AQI 28 （优）

留言：Hi!
```

## 项目结构

```
ybot/
  main.py          # 长驻服务模式（Cron 调度）
  send_now.py      # 单次发送脚本（GitHub Actions 使用）
  weather.py       # 天气 & AQI 数据获取
wechat_templates/
  test.template    # 微信模板消息格式参考
.github/workflows/
  daily-greeting.yml   # 正式每日问候（由 Google Cloud Scheduler 触发）
  test-greeting.yml    # 测试问候（push / 手动触发）
```

## 部署指南

### 1. 微信公众号配置

#### 获取测试账号（推荐）

无需正式公众号，使用微信提供的沙箱测试账号即可：

1. 访问[微信公众平台接口测试帐号](https://mp.weixin.qq.com/debug/cgi-bin/sandbox?t=sandbox/login)，微信扫码登录
2. 页面会自动分配 **appID** 和 **appsecret**，将它们填入 `.env` 文件的 `WECHAT_APPID` 和 `WECHAT_SECRET`
3. 在「模板消息接口」处新增测试模板。模板需要在微信页面手动填写，不能通过 API 创建。将以下内容复制到模板内容中：
   ```
   当地时间：{{local_time.DATA}}
   北京时间：{{remote_time.DATA}}

   今日天气：
      - {{city1_name.DATA}}：{{city1_weather.DATA}}
      - {{city2_name.DATA}}：{{city2_weather.DATA}}

   空气质量：
      - {{city1_name.DATA}}：{{city1_aqi.DATA}}
      - {{city2_name.DATA}}：{{city2_aqi.DATA}}

   留言：{{plus_sentence.DATA}}
   ```
   提交后记录生成的 **模板ID**，填入 `WECHAT_TEMPLATE_ID`
4. 在「测试号二维码」处让接收者扫码关注，页面会显示其 **OpenID**，填入 `WECHAT_USER_ID`

#### 使用正式公众号

1. 登录[微信公众平台](https://mp.weixin.qq.com/)
2. 获取 AppID 和 AppSecret
3. 在「模板消息」中创建模板，模板内容同上（需在微信页面手动填写）
4. 记录模板 ID

### 2. GitHub 仓库 Secrets

在仓库 **Settings > Secrets and variables > Actions > Secrets** 中添加：

| Secret | 说明 |
|---|---|
| `WECHAT_APPID` | 微信公众号 AppID |
| `WECHAT_SECRET` | 微信公众号 AppSecret |
| `WECHAT_USER_ID` | 正式接收者的 OpenID |
| `WECHAT_TEST_USER_ID` | 测试接收者的 OpenID |
| `WECHAT_TEMPLATE_ID` | 模板消息 ID |
| `DEFAULT_SENTENCE` | 默认留言（如不设置则为 "Hi!"） |
| `GH_PAT` | GitHub Fine-grained PAT（见下方） |
| `CITIES` | 城市列表，格式 `名称,纬度,经度`，多个用 `;` 分隔（如不设置则使用默认值） |
| `LOCAL_TIMEZONE` | 当地时区，如 `America/Indiana/Indianapolis`（如不设置则使用默认值） |
| `REMOTE_TIMEZONE` | 对方时区，如 `Asia/Shanghai`（如不设置则使用默认值） |

时区查询：[https://en.wikipedia.org/wiki/List_of_tz_database_time_zones](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)

#### 留言机制

- **`DEFAULT_SENTENCE`**：持久的默认留言，每次发送都会使用
- **`PLUS_SENTENCE`**：一次性留言，设置后下次**正式问候**发送时使用并自动删除，之后回退到 `DEFAULT_SENTENCE`
- **测试问候**不会消耗 `PLUS_SENTENCE`，可以放心用来预览

优先级：`PLUS_SENTENCE` > `DEFAULT_SENTENCE` > `"Hi!"`

### 4. 创建 GitHub Fine-grained PAT

1. 前往 [GitHub Settings > Developer settings > Personal access tokens > Fine-grained tokens](https://github.com/settings/tokens?type=beta)
2. 创建新 Token，选择此仓库
3. 权限设置：
   - **Actions**: Read and write（Cloud Scheduler 触发 workflow）
   - **Secrets**: Read and write（发送后自动删除 `PLUS_SENTENCE`）
4. 将生成的 Token 保存为仓库 Secret `GH_PAT`

### 5. 配置 Google Cloud Scheduler

Google Cloud Scheduler 通过 GitHub API 定时触发 `workflow_dispatch` 事件，替代 GitHub Actions 自带的 cron（后者不稳定）。

#### 前置条件

- 一个 Google Cloud 项目（有计费账号，Scheduler 免费额度为每月 3 个 Job）
- 安装 [gcloud CLI](https://cloud.google.com/sdk/docs/install)

#### 创建 Scheduler Job

```bash
# 登录并设置项目
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# 创建 Scheduler Job
# 以下示例为每天 UTC 00:00（北京时间 08:00）触发
gcloud scheduler jobs create http ybot-daily-greeting \
  --location=us-central1 \
  --schedule="0 0 * * *" \
  --time-zone="UTC" \
  --uri="https://api.github.com/repos/OWNER/REPO/actions/workflows/daily-greeting.yml/dispatches" \
  --http-method=POST \
  --headers="Authorization=Bearer YOUR_GH_PAT,Accept=application/vnd.github+json,X-GitHub-Api-Version=2026-03-10" \
  --message-body='{"ref":"main"}'
```

将上面的 `YOUR_PROJECT_ID`、`OWNER/REPO`、`YOUR_GH_PAT` 替换为实际值。

#### 验证

```bash
# 手动触发一次，确认是否正常
gcloud scheduler jobs run ybot-daily-greeting --location=us-central1
```

在 GitHub 仓库 **Actions** 页面确认 Daily Greeting workflow 被成功触发。

#### 修改调度时间

```bash
gcloud scheduler jobs update http ybot-daily-greeting \
  --location=us-central1 \
  --schedule="0 0 * * *" \
  --time-zone="UTC"
```

### 6. 本地开发

```bash
# 安装依赖
uv sync

# 创建 .env 文件
cat > .env << 'EOF'
WECHAT_APPID=your_appid
WECHAT_SECRET=your_secret
WECHAT_USER_ID=your_openid
WECHAT_TEMPLATE_ID=your_template_id
DEFAULT_SENTENCE=Hello!
CITIES=西拉法叶,40.4259,-86.9081;杭州,30.2741,120.1551
LOCAL_TIMEZONE=America/Indiana/Indianapolis
REMOTE_TIMEZONE=Asia/Shanghai
EOF

# 单次发送测试
uv run python -m ybot.send_now

# 长驻服务模式
uv run python -m ybot.main
```

## 工作流说明

| Workflow | 触发方式 | 接收者 | 消耗留言 |
|---|---|---|---|
| Daily Greeting | Google Cloud Scheduler / 手动 | `WECHAT_USER_ID` | 是 |
| Test Greeting | Push / 手动 | `WECHAT_TEST_USER_ID` | 否 |
