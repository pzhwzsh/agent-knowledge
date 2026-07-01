"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiRequest, Recommendation } from "../../lib/api";
import { useAuth } from "../../lib/auth";
import { AppShell, EmptyState, PageCard } from "../../components/AppShell";

export default function RecommendationsPage() {
  const router = useRouter();
  const auth = useAuth();
  const [items, setItems] = useState<Recommendation[]>([]);
  const [message, setMessage] = useState("");

  useEffect(() => { if (!auth.isLoading && !auth.token) router.push("/"); }, [auth.isLoading, auth.token, router]);
  useEffect(() => { if (auth.token) void load(); }, [auth.token]);

  async function load() { if (!auth.token) return; setItems(await apiRequest<Recommendation[]>("/api/recommendations", {}, auth.token)); }
  async function act(id: string, action: "save" | "ignore" | "dislike") { if (!auth.token) return; await apiRequest(`/api/recommendations/${id}/${action}`, { method: "POST" }, auth.token); setMessage(action === "save" ? "已保存到知识库。" : "推荐状态已更新。"); await load(); }

  return <AppShell user={auth.user} onSignOut={() => { auth.signOut(); router.push("/"); }}><PageCard><div><p className="text-sm text-cyan-100/70">Recommendations</p><h1 className="mt-2 text-3xl font-semibold">推荐箱</h1><p className="mt-2 text-sm text-slate-400">推荐不会自动入库，你可以保存、忽略或标记不感兴趣。</p></div>{message ? <p className="mt-4 rounded-2xl border border-white/10 bg-white/[0.06] p-3 text-sm">{message}</p> : null}<div className="mt-6 grid gap-4 md:grid-cols-2">{items.map((item) => <article className="rounded-3xl border border-white/10 bg-slate-950/35 p-5" key={item.id}><div className="flex items-start justify-between gap-3"><div><p className="text-xs text-slate-500">{item.category} · {item.status}</p><h2 className="mt-2 text-xl font-semibold">{item.summary || item.reason || `推荐内容 ${item.content_id.slice(0, 8)}`}</h2></div><span className="rounded-full bg-cyan-300/15 px-3 py-1 text-xs text-cyan-100">{Math.round(item.score * 100)}分</span></div><p className="mt-4 text-sm leading-6 text-slate-300">{item.reason || "系统根据你的偏好生成了这条推荐。"}</p><div className="mt-4 flex flex-wrap gap-2">{item.tags.map((tag) => <span className="rounded-full bg-white/10 px-2 py-1 text-xs" key={tag}>{tag}</span>)}</div><div className="mt-5 flex flex-wrap gap-2"><button className="rounded-full bg-cyan-300 px-4 py-2 text-sm font-semibold text-slate-950" onClick={() => void act(item.id, "save")}>保存</button><button className="rounded-full border border-white/10 px-4 py-2 text-sm" onClick={() => void act(item.id, "ignore")}>忽略</button><button className="rounded-full border border-white/10 px-4 py-2 text-sm" onClick={() => void act(item.id, "dislike")}>不感兴趣</button></div></article>)}{items.length === 0 ? <EmptyState text="暂无推荐。可以先通过 discovery 或内容提交生成推荐。" /> : null}</div></PageCard></AppShell>;
}
