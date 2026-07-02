"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiRequest, UserFeedback } from "../../lib/api";
import { useAuth } from "../../lib/auth";
import { AppShell, EmptyState, PageCard } from "../../components/AppShell";
import { SkeletonList, useQueryErrorToast } from "../../components/QueryState";
import { useToast } from "../../components/ToastProvider";

type FeedbackType = UserFeedback["feedback_type"];
type Severity = UserFeedback["severity"];

export default function FeedbackPage() {
  const router = useRouter();
  const auth = useAuth();
  const { notify } = useToast();
  const queryClient = useQueryClient();
  const [feature, setFeature] = useState("推荐");
  const [feedbackType, setFeedbackType] = useState<FeedbackType>("repair");
  const [severity, setSeverity] = useState<Severity>("medium");
  const [message, setMessage] = useState("");

  useEffect(() => { if (!auth.isLoading && !auth.token) router.push("/"); }, [auth.isLoading, auth.token, router]);

  const feedbackQuery = useQuery({
    queryKey: ["feedback", auth.token],
    enabled: Boolean(auth.token),
    queryFn: () => apiRequest<UserFeedback[]>("/api/feedback", {}, auth.token),
  });

  useQueryErrorToast({ error: feedbackQuery.error, fallbackMessage: "????????", isError: feedbackQuery.isError });

  const createMutation = useMutation({
    mutationFn: () => apiRequest<UserFeedback>("/api/feedback", { method: "POST", body: JSON.stringify({ feature, feedback_type: feedbackType, severity, message }) }, auth.token),
    onSuccess: async () => {
      setMessage("");
      notify("反馈已记录。后续会根据这些记录决定修复、调试或删除功能。", "success");
      await queryClient.invalidateQueries({ queryKey: ["feedback", auth.token] });
    },
    onError: (error) => notify(error instanceof Error ? error.message : "反馈提交失败", "error"),
  });

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!auth.token || !message.trim()) return;
    createMutation.mutate();
  }

  const items = feedbackQuery.data ?? [];
  const showInitialSkeleton = feedbackQuery.isLoading && items.length === 0;
  return <AppShell user={auth.user} onSignOut={() => { auth.signOut(); router.push("/"); }}><PageCard><div><p className="text-sm text-cyan-100/70">Feedback</p><h1 className="mt-2 text-3xl font-semibold">反馈维修台</h1><p className="mt-2 text-sm text-slate-400">记录实际使用中不好用、要修、要删或想增强的功能，后续按这些反馈调试和维修。</p></div><form className="mt-6 grid gap-4 rounded-3xl border border-white/10 bg-slate-950/35 p-5" onSubmit={submit}><label className="block"><span className="mb-2 block text-sm text-slate-300">功能模块</span><input className="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-sm outline-none" value={feature} onChange={(event) => setFeature(event.target.value)} placeholder="例如：推荐、搜索问答、采集、前端页面" /></label><div className="grid gap-4 md:grid-cols-2"><label className="block"><span className="mb-2 block text-sm text-slate-300">反馈类型</span><select className="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-sm outline-none" value={feedbackType} onChange={(event) => setFeedbackType(event.target.value as FeedbackType)}><option value="bug">出错</option><option value="repair">需要维修</option><option value="delete">建议删除</option><option value="idea">增强建议</option><option value="other">其他</option></select></label><label className="block"><span className="mb-2 block text-sm text-slate-300">严重程度</span><select className="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-sm outline-none" value={severity} onChange={(event) => setSeverity(event.target.value as Severity)}><option value="low">低</option><option value="medium">中</option><option value="high">高</option><option value="critical">严重</option></select></label></div><label className="block"><span className="mb-2 block text-sm text-slate-300">具体问题或建议</span><textarea className="min-h-32 w-full resize-none rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-sm outline-none" value={message} onChange={(event) => setMessage(event.target.value)} placeholder="描述你实际使用时遇到的问题、期望怎么修，或者为什么想删掉这个功能。" /></label><button className="rounded-2xl bg-cyan-300 px-5 py-3 text-sm font-semibold text-slate-950 disabled:opacity-50" disabled={!message.trim() || createMutation.isPending}>{createMutation.isPending ? "提交中" : "提交反馈"}</button></form><div className="mt-6 space-y-3"><h2 className="text-xl font-semibold">我的反馈记录</h2>{showInitialSkeleton ? <SkeletonList className="space-y-3" count={2} /> : items.map((item) => <article className="rounded-3xl border border-white/10 bg-slate-950/35 p-5" key={item.id}><div className="flex flex-wrap items-center justify-between gap-2"><h3 className="text-lg font-semibold">{item.feature}</h3><span className="rounded-full bg-white/10 px-3 py-1 text-xs">{item.feedback_type} · {item.severity} · {item.status}</span></div><p className="mt-3 text-sm leading-6 text-slate-300">{item.message}</p><p className="mt-3 text-xs text-slate-500">{new Date(item.created_at).toLocaleString()}</p></article>)}{!feedbackQuery.isLoading && items.length === 0 ? <EmptyState text="还没有反馈记录。" /> : null}</div></PageCard></AppShell>;
}
