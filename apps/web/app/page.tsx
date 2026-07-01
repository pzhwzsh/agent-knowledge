"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { apiRequest, TokenResponse, User } from "../lib/api";
import { storeToken } from "../lib/auth";

type AuthMode = "login" | "register";

export default function Home() {
  const router = useRouter();
  const [authMode, setAuthMode] = useState<AuthMode>("login");
  const [email, setEmail] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsLoading(true);
    setMessage("");
    try {
      if (authMode === "register") {
        await apiRequest<User>("/api/auth/register", {
          method: "POST",
          body: JSON.stringify({ email, password, display_name: displayName || null }),
        }, null);
      }
      const login = await apiRequest<TokenResponse>("/api/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      }, null);
      storeToken(login.access_token);
      router.push("/dashboard");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "认证失败，请稍后再试");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className="relative min-h-screen overflow-hidden bg-[#08111f] text-slate-100">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,rgba(56,189,248,0.22),transparent_32%),radial-gradient(circle_at_78%_12%,rgba(168,85,247,0.24),transparent_30%),radial-gradient(circle_at_50%_90%,rgba(20,184,166,0.18),transparent_38%)]" />
      <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.035)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.035)_1px,transparent_1px)] bg-[size:44px_44px] opacity-40" />
      <section className="relative mx-auto grid min-h-screen w-full max-w-7xl grid-cols-1 gap-8 px-5 py-6 sm:px-8 lg:grid-cols-[0.95fr_1.05fr] lg:px-10 lg:py-8">
        <div className="flex min-h-[680px] flex-col justify-between rounded-[2rem] border border-white/10 bg-white/[0.07] p-6 shadow-2xl shadow-cyan-950/40 backdrop-blur-2xl sm:p-8">
          <header className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="grid h-11 w-11 place-items-center rounded-2xl border border-cyan-200/30 bg-cyan-200/15 shadow-lg shadow-cyan-400/20"><span className="h-4 w-4 rounded-full bg-cyan-200 shadow-[0_0_24px_rgba(103,232,249,0.9)]" /></div>
              <div><p className="text-sm text-cyan-100/70">Personal Radar</p><h1 className="text-lg font-semibold tracking-wide">个人信息雷达</h1></div>
            </div>
            <span className="rounded-full border border-white/10 bg-white/10 px-3 py-1 text-xs text-cyan-50/80">API 已接入</span>
          </header>
          <div className="relative mx-auto my-10 grid h-72 w-72 place-items-center sm:h-80 sm:w-80">
            <div className="radar-sweep absolute inset-0 rounded-full border border-cyan-200/15 bg-cyan-200/[0.03]" />
            <div className="absolute inset-8 rounded-full border border-white/10" /><div className="absolute inset-16 rounded-full border border-white/10" />
            <div className="absolute h-px w-full bg-cyan-100/10" /><div className="absolute h-full w-px bg-cyan-100/10" />
            <FloatingDot className="left-16 top-12" label="RSS" /><FloatingDot className="right-10 top-28" label="GitHub" /><FloatingDot className="bottom-16 left-20" label="RAG" />
            <div className="z-10 rounded-[2rem] border border-white/15 bg-slate-950/70 p-5 text-center shadow-2xl shadow-cyan-500/20 backdrop-blur-xl"><p className="text-xs uppercase tracking-[0.35em] text-cyan-200/70">Live API</p><p className="mt-2 text-4xl font-semibold">ON</p><p className="mt-2 text-sm text-slate-300">登录后读取你的私有知识库</p></div>
          </div>
          <div className="rounded-[1.75rem] border border-white/10 bg-slate-950/55 p-5 shadow-xl shadow-slate-950/30 backdrop-blur-xl">
            <div className="mb-5 flex items-start justify-between gap-4">
              <div><p className="text-sm text-cyan-100/70">欢迎回来</p><h2 className="mt-1 text-3xl font-semibold tracking-tight">登录你的知识驾驶舱</h2><p className="mt-3 text-sm leading-6 text-slate-300">注册或登录后，可以进入仪表盘、推荐箱、文档库、搜索问答和偏好设置。</p></div>
              <div className="flex rounded-full border border-white/10 bg-white/[0.06] p-1 text-xs"><button className={`rounded-full px-3 py-1.5 transition ${authMode === "login" ? "bg-cyan-300 text-slate-950" : "text-slate-300"}`} type="button" onClick={() => setAuthMode("login")}>登录</button><button className={`rounded-full px-3 py-1.5 transition ${authMode === "register" ? "bg-cyan-300 text-slate-950" : "text-slate-300"}`} type="button" onClick={() => setAuthMode("register")}>注册</button></div>
            </div>
            <form className="space-y-4" onSubmit={handleSubmit}>
              {authMode === "register" ? <Input label="昵称" placeholder="例如：Xc305" value={displayName} onChange={setDisplayName} /> : null}
              <Input label="邮箱" placeholder="you@example.com" type="email" value={email} onChange={setEmail} required />
              <Input label="密码" placeholder="至少 8 位密码" type="password" value={password} onChange={setPassword} required minLength={8} />
              <button className="group relative w-full overflow-hidden rounded-2xl bg-cyan-300 px-5 py-3 font-semibold text-slate-950 shadow-lg shadow-cyan-400/25 transition hover:-translate-y-0.5 hover:bg-cyan-200 disabled:cursor-not-allowed disabled:opacity-60" disabled={isLoading} type="submit"><span className="relative z-10">{isLoading ? "处理中..." : authMode === "login" ? "进入个人雷达" : "创建并登录"}</span><span className="absolute inset-y-0 -left-1/3 w-1/3 skew-x-[-18deg] bg-white/60 transition duration-700 group-hover:left-full" /></button>
            </form>
            {message ? <p className="mt-4 rounded-2xl border border-white/10 bg-white/[0.06] px-4 py-3 text-sm text-slate-200">{message}</p> : null}
          </div>
        </div>
        <div className="flex min-h-[680px] flex-col justify-center rounded-[2rem] border border-white/10 bg-slate-950/35 p-8 shadow-2xl shadow-slate-950/50 backdrop-blur-2xl">
          <p className="text-sm text-cyan-100/70">完整工作台</p>
          <h2 className="mt-3 text-5xl font-semibold tracking-tight">把收藏、推荐、问答和偏好放到一个舒服的界面里。</h2>
          <div className="mt-8 grid gap-4 sm:grid-cols-2">{["仪表盘", "文档库", "推荐箱", "搜索问答", "偏好设置", "快速采集"].map((item) => <div className="rounded-3xl border border-white/10 bg-white/[0.07] p-5 text-slate-200" key={item}>{item}</div>)}</div>
        </div>
      </section>
    </main>
  );
}

function Input(props: { label: string; placeholder: string; value: string; onChange: (value: string) => void; type?: string; required?: boolean; minLength?: number }) {
  return <label className="block"><span className="mb-2 block text-sm text-slate-300">{props.label}</span><input className="w-full rounded-2xl border border-white/10 bg-white/[0.08] px-4 py-3 text-sm text-white outline-none transition placeholder:text-slate-500 focus:border-cyan-300/70 focus:bg-white/[0.12] focus:ring-4 focus:ring-cyan-300/10" minLength={props.minLength} placeholder={props.placeholder} required={props.required} type={props.type ?? "text"} value={props.value} onChange={(event) => props.onChange(event.target.value)} /></label>;
}

function FloatingDot({ className, label }: { className: string; label: string }) {
  return <div className={`absolute ${className} flex items-center gap-2 rounded-full border border-cyan-100/15 bg-slate-950/70 px-3 py-1.5 text-xs text-cyan-50 shadow-lg shadow-cyan-500/10 backdrop-blur-xl`}><span className="h-2 w-2 rounded-full bg-cyan-300 shadow-[0_0_16px_rgba(103,232,249,0.95)]" />{label}</div>;
}
