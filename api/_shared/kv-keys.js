// KV key 命名单一真源 · JS Edge 侧
//
// 对称镜像见 _build/arctura_mvp/store/keys.py（Python 侧）· 改一边必须改另一边。
// 有双端 snapshot 测试（_tests/kv-keys-cross-lang.spec.mjs）保护。

export const K = {
  project:          (slug) => `project:${slug}`,
  briefHistory:     (slug) => `project:${slug}:brief_history`,
  pendingEdits:     (slug) => `project:${slug}:pending_edits`,
  projectsIndex:    ()     => "projects:index",
  projectsArchive: ()     => "projects:archive",
  sessionProjects:  (anon) => `session:${anon}:projects`,
  rateIp:           (ip,     action = "create") => `rate:${ip}:${action}`,
  rateSession:      (anon,   action = "create") => `rate:session:${anon}:${action}`,
  lock:             (slug) => `project:${slug}:lock`,
  job:              (id)   => `job:${id}`,
  jobsQueue:        ()     => "jobs:queue",
  audit:            (slug, ts) => `audit:${slug}:${ts}`,
  migrationGuard:   (version)  => `migration:legacy:${version}`,
};
