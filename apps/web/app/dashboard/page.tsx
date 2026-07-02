"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FormEvent, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { apiRequest, DocumentItem, IngestionJob, IngestionQueueResponse, isLikelyUrl, Recommendation } from "../../lib/api";
import { useAuth } from "../../lib/auth";
import { AppShell, EmptyState, PageCard, SkeletonCard } from "../../components/AppShell";
import { useToast } from "../../components/ToastProvider";

type DashboardData = { documents: DocumentItem[]; recommendations: Recommendation[]; ingestions: IngestionJob[] };

const emptyDashboard: DashboardData = { documents: [], recommendations: [], ingestions: [] };

export default function DashboardPage() {
  const router = useRouter();
  const auth = useAuth();
  const { notify } = useToast();
  const queryClient = useQueryClient();
  const [newContent, setNewContent] = useState("");

  useEffect(() => { if (!auth.isLoading && !auth.token) router.push("/"); }, [auth.isLoading, auth.token, router]);

  const dashboardQuery = useQuery({
    queryKey: ["dashboard", auth.token],
    enabled: Boolean(auth.token),
    queryFn: async () => {
      const [documents, recommendations, ingestions] = await Promise.all([
        apiRequest<DocumentItem[]>("/api/documents", {}, auth.token),
        apiRequest<Recommendation[]>("/api/recommendations", {}, auth.token),
        apiRequest<IngestionJob[]>("/api/ingestions", {}, auth.token),
      ]);
      return { documents, recommendations, ingestions };
    },
  });
  const data = dashboardQuery.data ?? emptyDashboard;

  const submitMutation = useMutation({
    mutationFn: async () => apiRequest<IngestionQueueResponse>("/api/ingestions", { method: "POST", body: JSON.stringify({ input_type: isLikelyUrl(newContent) ? "url" : "text", input_value: newContent.trim() }) }, auth.token),
    onMutate: () => notify("正在提交给 Agent...", "info"),
    onSuccess: async (queued) => {
      setNewContent("");
      notify(queued.job.status === "failed" ? `提交失败：${queued.job.error_message ?? "任务未能入队"}` : `已创建采集任务 ${queued.job.id.slice(0, 8)}，后台处理中。`, queued.job.status === "failed" ? "error" : "success");
      await queryClient.invalidateQueries({ queryKey: ["dashboard", auth.token] });
    },
    onError: (error) => notify(error instanceof Error ? error.message : "提交失败", "error"),
  });

  const cards = useMemo(() => [
    { label: "知识文档", value: data.documents.length, color: "bg-cyan-300" },
    { label: "待处理推荐", value: data.recommendations.filter((item) => item.status === "pending").length, color: "bg-violet-300" },
    { label: "采集任务", value: data.ingestions.length, color: "bg-emerald-300" },
  ], [data]);

  async function submitContent(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!auth.token || !newContent.trim()) return;
    submitMutation.mutate();
  }

  const isLoading = dashboardQuery.isFetching;
  const showInitialSkeleton = dashboardQuery.isLoading && !dashboardQuery.data;
  return <AppShell user={auth.user} onSignOut={() => { auth.signOut(); router.push("/"); }}><PageCard><div className="flex flex-wrap items-start justify-between gap-4"><div><p className="text-sm text-cyan-100/70">Dashboard</p><h1 className="mt-2 text-3xl font-semibold">个人知识雷达仪表盘</h1><p className="mt-2 text-sm text-slate-400">实时读取你的文档、推荐和采集任务。</p></div><button className="rounded-full bg-cyan-300 px-4 py-2 text-sm font-semibold text-slate-950" onClick={() => void dashboardQuery.refetch()}>{isLoading ? "刷新中" : "刷新"}</button></div>{dashboardQuery.error ? <p className="mt-4 rounded-2xl border border-rose-200/20 bg-rose-500/10 p-3 text-sm text-rose-100">{dashboardQuery.error instanceof Error ? dashboardQuery.error.message : "加载失败"}</p> : null}<div className="mt-6 grid gap-4 md:grid-cols-3">{showInitialSkeleton ? ["documents", "recommendations", "ingestions"].map((item) => <SkeletonCard key={item} />) : cards.map((card) => <div className="rounded-3xl border border-white/10 bg-slate-950/35 p-5" key={card.label}><div className={`mb-6 h-1.5 w-16 rounded-full ${card.color}`} /><p className="text-sm text-slate-400">{card.label}</p><p className="mt-2 text-4xl font-semibold">{isLoading && !dashboardQuery.data ? "..." : card.value}</p></div>)}</div><div className="mt-6 grid gap-4 xl:grid-cols-[1.1fr_0.9fr]"><div className="rounded-3xl border border-white/10 bg-slate-950/35 p-5"><h2 className="text-xl font-semibold">快速采集</h2><form className="mt-4 space-y-3" onSubmit={submitContent}><textarea className="min-h-36 w-full resize-none rounded-3xl border border-white/10 bg-slate-950/60 p-4 text-sm outline-none focus:border-cyan-300/70" placeholder="粘贴 URL 或文本" value={newContent} onChange={(event) => setNewContent(event.target.value)} /><button className="rounded-2xl bg-cyan-300 px-5 py-3 text-sm font-semibold text-slate-950 disabled:opacity-50" disabled={!newContent.trim() || submitMutation.isPending}>{submitMutation.isPending ? "提交中" : "提交采集"}</button></form></div><div className="space-y-4"><MiniList title="最近文档" empty="暂无文档" items={data.documents.slice(0, 3).map((item) => item.title)} /><MiniList title="最新推荐" empty="暂无推荐" items={data.recommendations.slice(0, 3).map((item) => item.summary || item.reason || item.content_id)} /></div></div></PageCard></AppShell>;
}

function MiniList({ title, empty, items }: { title: string; empty: string; items: string[] }) { return <div className="rounded-3xl border border-white/10 bg-slate-950/35 p-5"><h2 className="text-lg font-semibold">{title}</h2><div className="mt-4 space-y-3">{items.map((item) => <div className="rounded-2xl border border-white/10 bg-white/[0.05] p-3 text-sm" key={item}>{item}</div>)}{items.length === 0 ? <EmptyState text={empty} /> : null}</div></div>; }
