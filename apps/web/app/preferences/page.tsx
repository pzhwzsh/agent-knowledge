"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiRequest, Preference } from "../../lib/api";
import { useAuth } from "../../lib/auth";
import { AppShell, PageCard } from "../../components/AppShell";

export default function PreferencesPage() {
  const router = useRouter();
  const auth = useAuth();
  const [preference, setPreference] = useState<Preference | null>(null);
  const [interests, setInterests] = useState("");
  const [negative, setNegative] = useState("");
  const [categories, setCategories] = useState("");
  const [dailyLimit, setDailyLimit] = useState(10);
  const [pushChannel, setPushChannel] = useState("in_app");
  const [message, setMessage] = useState("");

  useEffect(() => { if (!auth.isLoading && !auth.token) router.push("/"); }, [auth.isLoading, auth.token, router]);
  useEffect(() => { if (auth.token) void load(); }, [auth.token]);

  async function load() {
    if (!auth.token) return;
    const data = await apiRequest<Preference>("/api/preferences", {}, auth.token);
    setPreference(data);
    setInterests(data.interests.join(", "));
    setNegative(data.negative_interests.join(", "));
    setCategories(data.enabled_categories.join(", "));
    setDailyLimit(data.daily_limit);
    setPushChannel(data.push_channel);
  }

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!auth.token) return;
    const updated = await apiRequest<Preference>("/api/preferences", { method: "PUT", body: JSON.stringify({ interests: splitList(interests), negative_interests: splitList(negative), enabled_categories: splitList(categories), daily_limit: dailyLimit, push_channel: pushChannel }) }, auth.token);
    setPreference(updated);
    setMessage("偏好已保存。推荐流程会基于这些配置评分。");
  }

  return <AppShell user={auth.user} onSignOut={() => { auth.signOut(); router.push("/"); }}><PageCard><div><p className="text-sm text-cyan-100/70">Preferences</p><h1 className="mt-2 text-3xl font-semibold">个人偏好设置</h1><p className="mt-2 text-sm text-slate-400">配置兴趣、不感兴趣关键词、分类和每日推荐数量。</p></div>{message ? <p className="mt-4 rounded-2xl border border-white/10 bg-white/[0.06] p-3 text-sm">{message}</p> : null}<form className="mt-6 grid gap-4" onSubmit={save}><Field label="兴趣关键词" value={interests} onChange={setInterests} placeholder="AI Agent, RAG, GitHub" /><Field label="不感兴趣关键词" value={negative} onChange={setNegative} placeholder="广告, 水文" /><Field label="启用分类" value={categories} onChange={setCategories} placeholder="article, github, career" /><label className="block"><span className="mb-2 block text-sm text-slate-300">推送渠道</span><select className="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-sm outline-none" value={pushChannel} onChange={(event) => setPushChannel(event.target.value)}><option value="in_app">站内</option><option value="email">邮件</option><option value="dingtalk">钉钉</option></select></label><label className="block"><span className="mb-2 block text-sm text-slate-300">每日推荐上限</span><input className="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-sm outline-none" max={100} min={1} type="number" value={dailyLimit} onChange={(event) => setDailyLimit(Number(event.target.value))} /></label><button className="rounded-2xl bg-cyan-300 px-5 py-3 text-sm font-semibold text-slate-950">保存偏好</button></form>{preference ? <p className="mt-5 text-xs text-slate-500">当前偏好 ID：{preference.id}</p> : null}</PageCard></AppShell>;
}

function Field({ label, value, placeholder, onChange }: { label: string; value: string; placeholder: string; onChange: (value: string) => void }) { return <label className="block"><span className="mb-2 block text-sm text-slate-300">{label}</span><input className="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-sm outline-none" placeholder={placeholder} value={value} onChange={(event) => onChange(event.target.value)} /></label>; }
function splitList(value: string) { return value.split(/[,，]/).map((item) => item.trim()).filter(Boolean); }
