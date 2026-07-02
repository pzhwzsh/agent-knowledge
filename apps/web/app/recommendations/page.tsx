"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { apiRequest, Recommendation } from "../../lib/api";
import { useAuth } from "../../lib/auth";
import { AppShell, EmptyState, PageCard } from "../../components/AppShell";
import { SkeletonList, useQueryErrorToast } from "../../components/QueryState";
import { useToast } from "../../components/ToastProvider";

export default function RecommendationsPage() {
  const router = useRouter();
  const auth = useAuth();
  const { notify } = useToast();
  const queryClient = useQueryClient();

  useEffect(() => { if (!auth.isLoading && !auth.token) router.push("/"); }, [auth.isLoading, auth.token, router]);

  const recommendationsQuery = useQuery({
    queryKey: ["recommendations", auth.token],
    enabled: Boolean(auth.token),
    queryFn: () => apiRequest<Recommendation[]>("/api/recommendations", {}, auth.token),
  });

  useQueryErrorToast({ error: recommendationsQuery.error, fallbackMessage: "??????", isError: recommendationsQuery.isError });

  const actionMutation = useMutation({
    mutationFn: async ({ id, action }: { id: string; action: "save" | "ignore" | "dislike" }) => {
      await apiRequest(`/api/recommendations/${id}/${action}`, { method: "POST" }, auth.token);
      return action;
    },
    onSuccess: async (action) => {
      notify(action === "save" ? "已保存到知识库。" : "推荐状态已更新。后续相似推荐会参考这次反馈。", "success");
      await queryClient.invalidateQueries({ queryKey: ["recommendations", auth.token] });
      await queryClient.invalidateQueries({ queryKey: ["dashboard", auth.token] });
    },
    onError: (error) => notify(error instanceof Error ? error.message : "操作失败", "error"),
  });

  const items = recommendationsQuery.data ?? [];
  const showInitialSkeleton = recommendationsQuery.isLoading && items.length === 0;
  function act(id: string, action: "save" | "ignore" | "dislike") { if (!auth.token) return; actionMutation.mutate({ id, action }); }

  return <AppShell user={auth.user} onSignOut={() => { auth.signOut(); router.push("/"); }}><PageCard><div className="flex flex-wrap items-start justify-between gap-4"><div><p className="text-sm text-cyan-100/70">Recommendations</p><h1 className="mt-2 text-3xl font-semibold">推荐箱</h1><p className="mt-2 text-sm text-slate-400">推荐不会自动入库，你可以保存、忽略或标记不感兴趣；系统会把这些反馈用于后续推荐评分。</p></div><button className="rounded-full bg-cyan-300 px-4 py-2 text-sm font-semibold text-slate-950" onClick={() => void recommendationsQuery.refetch()}>{recommendationsQuery.isFetching ? "刷新中" : "刷新"}</button></div>{recommendationsQuery.error ? <p className="mt-4 rounded-2xl border border-rose-200/20 bg-rose-500/10 p-3 text-sm text-rose-100">{recommendationsQuery.error instanceof Error ? recommendationsQuery.error.message : "推荐加载失败"}</p> : null}<div className="mt-6 grid gap-4 md:grid-cols-2">{showInitialSkeleton ? <SkeletonList className="contents" count={4} /> : items.map((item) => <article className="rounded-3xl border border-white/10 bg-slate-950/35 p-5" key={item.id}><div className="flex items-start justify-between gap-3"><div><p className="text-xs text-slate-500">{item.category} · {item.status}</p><h2 className="mt-2 text-xl font-semibold">{item.summary || item.reason || `推荐内容 ${item.content_id.slice(0, 8)}`}</h2></div><span className="rounded-full bg-cyan-300/15 px-3 py-1 text-xs text-cyan-100">{Math.round(item.score * 100)}分</span></div><p className="mt-4 text-sm leading-6 text-slate-300">{item.reason || "系统根据你的偏好生成了这条推荐。"}</p><div className="mt-4 flex flex-wrap gap-2">{item.tags.map((tag) => <span className="rounded-full bg-white/10 px-2 py-1 text-xs" key={tag}>{tag}</span>)}</div><div className="mt-5 flex flex-wrap gap-2"><button className="rounded-full bg-cyan-300 px-4 py-2 text-sm font-semibold text-slate-950 disabled:opacity-50" disabled={actionMutation.isPending} onClick={() => void act(item.id, "save")}>保存</button><button className="rounded-full border border-white/10 px-4 py-2 text-sm disabled:opacity-50" disabled={actionMutation.isPending} onClick={() => void act(item.id, "ignore")}>忽略</button><button className="rounded-full border border-white/10 px-4 py-2 text-sm disabled:opacity-50" disabled={actionMutation.isPending} onClick={() => void act(item.id, "dislike")}>不感兴趣</button></div></article>)}{!recommendationsQuery.isLoading && items.length === 0 ? <EmptyState text="暂无推荐。可以先通过 discovery 或内容提交生成推荐。" /> : null}</div></PageCard></AppShell>;
}
