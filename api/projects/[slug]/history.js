// GET /api/projects/<slug>/history · Phase 7.5
// 列 data/mvps/<slug>.json 的 GitHub commit 历史 · 每 commit 对应一个"brief 版本"
// 客户修订流程（spec L324-348）· 用 git 作 version store · 不重复造轮子
//
// 响应：{ commits: [{sha, date, message, url}] }
// 回滚（留 Phase 7.6+）：由前端提示用户去 GitHub compare/restore · 或将来补 POST restore

export const config = { runtime: "edge" };

const GITHUB_TOKEN = process.env.GITHUB_TOKEN;
const GH_OWNER = "YonganZhang";
const GH_REPO = "arctura-front-end";
const SLUG_SAFE = /^[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}$/;

function json(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store" },
  });
}

function getSlug(req) {
  const m = new URL(req.url).pathname.match(/\/api\/projects\/([^/]+)\/history/);
  return m ? decodeURIComponent(m[1]) : null;
}

export default async function handler(req) {
  if (req.method !== "GET") return json({ error: "method not allowed" }, 405);

  const slug = getSlug(req);
  if (!slug || !SLUG_SAFE.test(slug)) return json({ error: "bad slug" }, 400);

  if (!GITHUB_TOKEN) {
    return json({
      commits: [],
      _note: "GITHUB_TOKEN 未配 · 无法查 git 历史 · 修订流程降级到"只 KV"模式",
    });
  }

  const filePath = `data/mvps/${slug}.json`;
  const url = new URL(`https://api.github.com/repos/${GH_OWNER}/${GH_REPO}/commits`);
  url.searchParams.set("path", filePath);
  url.searchParams.set("per_page", "20");

  try {
    const resp = await fetch(url.toString(), {
      headers: {
        Authorization: `Bearer ${GITHUB_TOKEN}`,
        Accept: "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "arctura-history",
      },
    });

    if (resp.status === 404) {
      return json({ commits: [], _note: "该 slug 尚无提交记录（还未 save 过）" });
    }
    if (!resp.ok) {
      const t = await resp.text();
      return json({ error: `gh ${resp.status}`, detail: t.slice(0, 200) }, 502);
    }

    const data = await resp.json();
    const commits = data.map(c => ({
      sha: c.sha,
      short_sha: c.sha.slice(0, 7),
      date: c.commit.committer.date,
      message: c.commit.message,
      author: c.commit.committer.name,
      html_url: c.html_url,
      // 用户可以拷这个 URL 在 GitHub UI "Revert" / 看 diff
      compare_with_prev: `https://github.com/${GH_OWNER}/${GH_REPO}/commit/${c.sha}`,
    }));

    return json({
      commits,
      slug,
      file_path: filePath,
      github_history_url: `https://github.com/${GH_OWNER}/${GH_REPO}/commits/main/${filePath}`,
    });
  } catch (e) {
    return json({ error: "gh fetch failed", detail: String(e.message || e) }, 502);
  }
}
