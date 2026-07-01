"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiRequest, DocumentItem, DocumentWithChunks } from "../../lib/api";
import { useAuth } from "../../lib/auth";
import { AppShell, EmptyState, PageCard } from "../../components/AppShell";

export default function DocumentsPage() {
  const router = useRouter();
  const auth = useAuth();
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [selected, setSelected] = useState<DocumentWithChunks | null>(null);
  const [message, setMessage] = useState("");

  useEffect(() => { if (!auth.isLoading && !auth.token) router.push("/"); }, [auth.isLoading, auth.token, router]);
  useEffect(() => { if (auth.token) void loadDocuments(); }, [auth.token]);

  async function loadDocuments() {
    if (!auth.token) return;
    const data = await apiRequest<DocumentItem[]>("/api/documents", {}, auth.token);
    setDocuments(data);
    if (!selected && data[0]) void openDocument(data[0].id);
  }

  async function openDocument(id: string) {
    if (!auth.token) return;
    setMessage("");
    const detail = await apiRequest<DocumentWithChunks>(`/api/documents/${id}`, {}, auth.token);
    setSelected(detail);
  }

  async function deleteDocument(id: string) {
    if (!auth.token) return;
    await apiRequest(`/api/documents/${id}`, { method: "DELETE" }, auth.token);
    setSelected(null);
    setMessage("文档已删除。");
    await loadDocuments();
  }

  return <AppShell user={auth.user} onSignOut={() => { auth.signOut(); router.push("/"); }}><PageCard><div><p className="text-sm text-cyan-100/70">Documents</p><h1 className="mt-2 text-3xl font-semibold">我的知识库文档</h1><p className="mt-2 text-sm text-slate-400">查看当前用户私有文档、切片数量和标签。</p></div>{message ? <p className="mt-4 rounded-2xl border border-white/10 bg-white/[0.06] p-3 text-sm">{message}</p> : null}<div className="mt-6 grid gap-4 lg:grid-cols-[0.9fr_1.1fr]"><div className="space-y-3">{documents.map((document) => <button className="w-full rounded-3xl border border-white/10 bg-slate-950/35 p-4 text-left transition hover:border-cyan-200/40" key={document.id} type="button" onClick={() => void openDocument(document.id)}><p className="font-medium">{document.title}</p><p className="mt-2 text-xs text-slate-500">{document.category} · {document.source_type}</p><div className="mt-3 flex flex-wrap gap-2">{document.tags.slice(0, 4).map((tag) => <span className="rounded-full bg-white/10 px-2 py-1 text-xs" key={tag}>{tag}</span>)}</div></button>)}{documents.length === 0 ? <EmptyState text="暂无文档。先去仪表盘提交内容，或在推荐箱保存推荐。" /> : null}</div><div className="rounded-3xl border border-white/10 bg-slate-950/35 p-5">{selected ? <div><div className="flex items-start justify-between gap-4"><div><h2 className="text-2xl font-semibold">{selected.title}</h2><p className="mt-2 text-sm text-slate-400">{selected.source_url || "无来源链接"}</p></div><button className="rounded-full border border-rose-200/30 px-4 py-2 text-sm text-rose-100" type="button" onClick={() => void deleteDocument(selected.id)}>删除</button></div><p className="mt-5 text-sm leading-6 text-slate-300">{selected.summary || selected.long_summary || "暂无摘要。"}</p><h3 className="mt-6 text-lg font-semibold">切片</h3><div className="mt-3 space-y-3">{selected.chunks.slice(0, 5).map((chunk) => <div className="rounded-2xl border border-white/10 bg-white/[0.05] p-4 text-sm leading-6 text-slate-300" key={chunk.id}>{chunk.content}</div>)}</div></div> : <EmptyState text="选择左侧文档查看详情。" />}</div></div></PageCard></AppShell>;
}
