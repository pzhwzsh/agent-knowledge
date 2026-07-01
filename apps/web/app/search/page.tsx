"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiRequest, ChatResponse, SearchResult } from "../../lib/api";
import { useAuth } from "../../lib/auth";
import { AppShell, EmptyState, PageCard } from "../../components/AppShell";

export default function SearchPage() {
  const router = useRouter();
  const auth = useAuth();
  const [query, setQuery] = useState("");
  const [question, setQuestion] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [chat, setChat] = useState<ChatResponse | null>(null);
  const [message, setMessage] = useState("");

  useEffect(() => { if (!auth.isLoading && !auth.token) router.push("/"); }, [auth.isLoading, auth.token, router]);

  async function search(event: FormEvent<HTMLFormElement>) { event.preventDefault(); if (!auth.token || !query.trim()) return; setMessage("搜索中..."); try { const data = await apiRequest<{ results: SearchResult[] }>("/api/search", { method: "POST", body: JSON.stringify({ query, limit: 8 }) }, auth.token); setResults(data.results); setMessage(""); } catch (error) { setMessage(error instanceof Error ? error.message : "搜索失败"); } }
  async function ask(event: FormEvent<HTMLFormElement>) { event.preventDefault(); if (!auth.token || !question.trim()) return; setMessage("正在问答..."); try { setChat(await apiRequest<ChatResponse>("/api/chat", { method: "POST", body: JSON.stringify({ question, limit: 5 }) }, auth.token)); setMessage(""); } catch (error) { setMessage(error instanceof Error ? error.message : "问答失败"); } }

  return <AppShell user={auth.user} onSignOut={() => { auth.signOut(); router.push("/"); }}><PageCard><div><p className="text-sm text-cyan-100/70">Search & Chat</p><h1 className="mt-2 text-3xl font-semibold">搜索和知识库问答</h1><p className="mt-2 text-sm text-slate-400">只会检索当前登录用户自己的文档切片。</p></div>{message ? <p className="mt-4 rounded-2xl border border-white/10 bg-white/[0.06] p-3 text-sm">{message}</p> : null}<div className="mt-6 grid gap-4 xl:grid-cols-2"><section className="rounded-3xl border border-white/10 bg-slate-950/35 p-5"><h2 className="text-xl font-semibold">语义搜索</h2><form className="mt-4 flex gap-2" onSubmit={search}><input className="min-w-0 flex-1 rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-sm outline-none" placeholder="搜索你的知识库" value={query} onChange={(event) => setQuery(event.target.value)} /><button className="rounded-2xl bg-cyan-300 px-5 py-3 text-sm font-semibold text-slate-950">搜索</button></form><div className="mt-4 space-y-3">{results.map((item) => <div className="rounded-2xl border border-white/10 bg-white/[0.05] p-4" key={item.chunk_id}><div className="flex justify-between gap-3"><p className="font-medium">{item.title}</p><span className="text-xs text-cyan-100">{item.score.toFixed(3)}</span></div><p className="mt-2 text-sm leading-6 text-slate-300">{item.content}</p></div>)}{results.length === 0 ? <EmptyState text="输入关键词后查看语义搜索结果。" /> : null}</div></section><section className="rounded-3xl border border-white/10 bg-slate-950/35 p-5"><h2 className="text-xl font-semibold">带引用问答</h2><form className="mt-4 space-y-3" onSubmit={ask}><textarea className="min-h-28 w-full resize-none rounded-3xl border border-white/10 bg-slate-950/60 p-4 text-sm outline-none" placeholder="向你的知识库提问" value={question} onChange={(event) => setQuestion(event.target.value)} /><button className="rounded-2xl bg-cyan-300 px-5 py-3 text-sm font-semibold text-slate-950">提问</button></form>{chat ? <div className="mt-4 rounded-2xl border border-white/10 bg-white/[0.05] p-4"><p className="text-sm leading-6 text-slate-200">{chat.answer}</p><div className="mt-4 space-y-2">{chat.citations.map((citation) => <div className="rounded-xl bg-slate-950/50 p-3 text-xs text-slate-400" key={citation.chunk_id}>引用：{citation.title}</div>)}</div></div> : <EmptyState text="提问后这里会显示答案和引用。" />}</section></div></PageCard></AppShell>;
}
