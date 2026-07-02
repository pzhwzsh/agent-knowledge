"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiRequest, Preference } from "../../lib/api";
import { useAuth } from "../../lib/auth";
import { AppShell, PageCard, SkeletonCard } from "../../components/AppShell";
import { useToast } from "../../components/ToastProvider";

export default function PreferencesPage() {
  const router = useRouter();
  const auth = useAuth();
  const { notify } = useToast();
  const queryClient = useQueryClient();
  const [interests, setInterests] = useState("");
  const [negative, setNegative] = useState("");
  const [categories, setCategories] = useState("");
  const [dailyLimit, setDailyLimit] = useState(10);
  const [pushChannel, setPushChannel] = useState("in_app");

  useEffect(() => { if (!auth.isLoading && !auth.token) router.push("/"); }, [auth.isLoading, auth.token, router]);

  const preferenceQuery = useQuery({
    queryKey: ["preferences", auth.token],
    enabled: Boolean(auth.token),
    queryFn: () => apiRequest<Preference>("/api/preferences", {}, auth.token),
  });

  useEffect(() => {
    if (!preferenceQuery.data) return;
    setInterests(preferenceQuery.data.interests.join(", "));
    setNegative(preferenceQuery.data.negative_interests.join(", "));
    setCategories(preferenceQuery.data.enabled_categories.join(", "));
    setDailyLimit(preferenceQuery.data.daily_limit);
    setPushChannel(preferenceQuery.data.push_channel);
  }, [preferenceQuery.data]);

  useEffect(() => {
    if (preferenceQuery.isError) notify(preferenceQuery.error instanceof Error ? preferenceQuery.error.message : "偏好加载失败", "error");
  }, [notify, preferenceQuery.error, preferenceQuery.isError]);

  const saveMutation = useMutation({
    mutationFn: () => apiRequest<Preference>("/api/preferences", { method: "PUT", body: JSON.stringify({ interests: splitList(interests), negative_interests: splitList(negative), enabled_categories: splitList(categories), daily_limit: dailyLimit, push_channel: pushChannel }) }, auth.token),
    onSuccess: async (updated) => {
      notify("偏好已保存。推荐流程会基于这些配置评分。", "success");
      queryClient.setQueryData(["preferences", auth.token], updated);
      await queryClient.invalidateQueries({ queryKey: ["recommendations", auth.token] });
      await queryClient.invalidateQueries({ queryKey: ["dashboard", auth.token] });
    },
    onError: (error) => notify(error instanceof Error ? error.message : "偏好保存失败", "error"),
  });

  function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!auth.token) return;
    saveMutation.mutate();
  }

  return <AppShell user={auth.user} onSignOut={() => { auth.signOut(); router.push("/"); }}><PageCard><div><p className="text-sm text-cyan-100/70">Preferences</p><h1 className="mt-2 text-3xl font-semibold">个人偏好设置</h1><p className="mt-2 text-sm text-slate-400">配置兴趣、不感兴趣关键词、分类和每日推荐数量。</p></div>{preferenceQuery.isLoading ? <div className="mt-6"><SkeletonCard /></div> : <form className="mt-6 grid gap-4" onSubmit={save}><Field label="兴趣关键词" value={interests} onChange={setInterests} placeholder="AI Agent, RAG, GitHub" /><Field label="不感兴趣关键词" value={negative} onChange={setNegative} placeholder="广告, 水文" /><Field label="启用分类" value={categories} onChange={setCategories} placeholder="article, github, career" /><label className="block"><span className="mb-2 block text-sm text-slate-300">推送渠道</span><select className="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-sm outline-none" value={pushChannel} onChange={(event) => setPushChannel(event.target.value)}><option value="in_app">站内</option><option value="email">邮件</option><option value="dingtalk">钉钉</option><option value="disabled">关闭推送</option></select></label><label className="block"><span className="mb-2 block text-sm text-slate-300">每日推荐上限</span><input className="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-sm outline-none" max={100} min={1} type="number" value={dailyLimit} onChange={(event) => setDailyLimit(Number(event.target.value))} /></label><button className="rounded-2xl bg-cyan-300 px-5 py-3 text-sm font-semibold text-slate-950 disabled:opacity-50" disabled={saveMutation.isPending}>{saveMutation.isPending ? "保存中" : "保存偏好"}</button></form>}{preferenceQuery.data ? <p className="mt-5 text-xs text-slate-500">当前偏好 ID：{preferenceQuery.data.id}</p> : null}</PageCard></AppShell>;
}

function Field({ label, value, placeholder, onChange }: { label: string; value: string; placeholder: string; onChange: (value: string) => void }) { return <label className="block"><span className="mb-2 block text-sm text-slate-300">{label}</span><input className="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-sm outline-none" placeholder={placeholder} value={value} onChange={(event) => onChange(event.target.value)} /></label>; }
function splitList(value: string) { return value.split(/[,，]/).map((item) => item.trim()).filter(Boolean); }
