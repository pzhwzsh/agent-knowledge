"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiRequest, DocumentItem, DocumentWithChunks } from "../../lib/api";
import { useAuth } from "../../lib/auth";
import { AppShell, EmptyState, PageCard, SkeletonCard } from "../../components/AppShell";
import { useToast } from "../../components/ToastProvider";

export default function DocumentsPage() {
  const router = useRouter();
  const auth = useAuth();
  const { notify } = useToast();
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [selected, setSelected] = useState<DocumentWithChunks | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => { if (!auth.isLoading && !auth.token) router.push("/"); }, [auth.isLoading, auth.token, router]);
  useEffect(() => { if (auth.token) void loadDocuments(); }, [auth.token]);

  async function loadDocuments() {
    if (!auth.token) return;
    setIsLoading(true);
    try {
      const data = await apiRequest<DocumentItem[]>("/api/documents", {}, auth.token);
      setDocuments(data);
      if (!selected && data[0]) void openDocument(data[0].id);
    } catch (error) {
      notify(error instanceof Error ? error.message : "文档加载失败", "error");
    } finally {
      setIsLoading(false);
    }
  }

  async function openDocument(id: string) {
    if (!auth.token) return;
    try {
      const detail = await apiRequest<DocumentWithChunks>(`/api/documents/${id}`, {}, auth.token);
      setSelected(detail);
    } catch (error) {
      notify(error instanceof Error ? error.message : "文档详情加载失败", "error");
    }
  }

  async function deleteDocument(id: string) {
    if (!auth.token) return;
    try {
      await apiRequest(`/api/documents/${id}`, { method: "DELETE" }, auth.token);
      setSelected(null);
      notify("文档已删除。", "success");
      await loadDocuments();
    } catch (error) {
      notify(error instanceof Error ? error.message : "文档删除失败", "error");
    }
  }

  return <AppShell user={auth.user} onSignOut={() => { auth.signOut(); router.push("/"); }}><PageCard><div><p className="text-sm text-cyan-100/70">Documents</p><h1 className="mt-2 text-3xl font-semibold">我的知识库文档</h1><p className="mt-2 text-sm text-slate-400">查看当前用户私有文档、切片数量和标签。</p></div><div className="mt-6 grid gap-4 lg:grid-cols-[0.9fr_1.1fr]"><div className="space-y-3">{isLoading && documents.length === 0 ? ["a", "b", "c"].map((item) => <SkeletonCard key={item} />) : documents.map((document) => <button className="w-full rounded-3xl border border-white/10 bg-slate-950/35 p-4 text-left transition hover:border-cyan-200/40" key={document.id} type="button" onClick={() => void openDocument(document.id)}><p className="font-medium">{document.title}</p><p className="mt-2 text-xs text-slate-500">{document.category} · {document.source_type}</p><div className="mt-3 flex flex-wrap gap-2">{document.tags.slice(0, 4).map((tag) => <span className="rounded-full bg-white/10 px-2 py-1 text-xs" key={tag}>{tag}</span>)}</div></button>)}{!isLoading && documents.length === 0 ? <EmptyState text="暂无文档。先去仪表盘提交内容，或在推荐箱保存推荐。" /> : null}</div><div className="rounded-3xl border border-white/10 bg-slate-950/35 p-5">{selected ? <div><div className="flex items-start justify-between gap-4"><div><h2 className="text-2xl font-semibold">{selected.title}</h2><p className="mt-2 text-sm text-slate-400">{selected.source_url || "无来源链接"}</p></div><button className="rounded-full border border-rose-200/30 px-4 py-2 text-sm text-rose-100" type="button" onClick={() => void deleteDocument(selected.id)}>删除</button></div><p className="mt-5 text-sm leading-6 text-slate-300">{selected.summary || selected.long_summary || "暂无摘要。"}</p><h3 className="mt-6 text-lg font-semibold">切片</h3><div className="mt-3 space-y-3">{selected.chunks.slice(0, 5).map((chunk) => <div className="rounded-2xl border border-white/10 bg-white/[0.05] p-4 text-sm leading-6 text-slate-300" key={chunk.id}>{chunk.content}</div>)}</div></div> : <EmptyState text="选择左侧文档查看详情。" />}</div></div></PageCard></AppShell>;
}
