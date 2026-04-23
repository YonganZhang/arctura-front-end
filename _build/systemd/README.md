# Systemd user units · Arctura Worker

## arctura-worker.service

MVP 生成 worker 的 systemd user 单元 · 在本机（如 tencent-hk）常驻跑。

### 安装（每台 worker 机跑一次）

```bash
# 1. 拷 unit 到 user 目录
mkdir -p ~/.config/systemd/user
cp _build/systemd/arctura-worker.service ~/.config/systemd/user/

# 2. reload + enable + start
systemctl --user daemon-reload
systemctl --user enable --now arctura-worker.service

# 3.（可选）开 linger · 让 user service 在未登录时也跑
#    需要 sudo · 跨用户会话持久化
sudo loginctl enable-linger $USER
```

### 常用命令

```bash
# 查状态
systemctl --user status arctura-worker

# 实时日志
journalctl --user -u arctura-worker -f

# 重启（拉新代码后）
systemctl --user restart arctura-worker

# 停 / 关自启
systemctl --user stop arctura-worker
systemctl --user disable arctura-worker
```

### 前置条件

- `~/.arctura-env` 存在 · 含 `UPSTASH_REDIS_REST_URL/TOKEN`
- Python 3.11+ · Node 20+（Playwright 用）
- 本机 repo clone 在 `~/projects/公司项目/Building-CLI-Anything/Arctura-Front-end/`
  （unit 里写死 · 换机需改 `WorkingDirectory=`）

### 资源限制

- `MemoryMax=2G` · 防 Playwright Chromium 爆内存拖死机器
- `CPUQuota=200%` · 最多用两核
- `Restart=always` + `RestartSec=5s` · 崩了 5 秒自动拉

### 注意

- 本 unit 是 **user-level**（不需 sudo）· 遵守 `share-shared-server` 红线
- `~/.arctura-env` 用 `export KEY=VALUE` 格式（给 bash source 用）· 不能直接
  `EnvironmentFile=` · 所以 ExecStart 走 `bash -lc 'source ... && exec python3 ...'`
- 改了 env / unit 文件后必 `daemon-reload` + `restart` · 否则不生效
