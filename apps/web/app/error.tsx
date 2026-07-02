"use client";

import { useEffect } from "react";

export default function ErrorBoundary({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  useEffect(() => {
    console.error("Application error boundary caught:", error);
  }, [error]);

  return (
    <main className="grid min-h-screen place-items-center bg-[#08111f] px-5 text-slate-100">
      <section className="w-full max-w-xl rounded-[2rem] border border-white/10 bg-white/[0.07] p-8 text-center shadow-2xl shadow-slate-950/40 backdrop-blur-2xl">
        <p className="text-sm text-cyan-100/70">Error Boundary</p>
        <h1 className="mt-3 text-3xl font-semibold">页面暂时出错了</h1>
        <p className="mt-3 text-sm leading-6 text-slate-400">系统已经拦截这次前端异常，你可以重试当前页面；如果重复出现，请到反馈维修台提交问题。</p>
        {error.digest ? <p className="mt-4 rounded-2xl border border-white/10 bg-slate-950/45 p-3 text-xs text-slate-500">错误编号：{error.digest}</p> : null}
        <div className="mt-6 flex flex-wrap justify-center gap-3">
          <button className="rounded-2xl bg-cyan-300 px-5 py-3 text-sm font-semibold text-slate-950" type="button" onClick={reset}>重试页面</button>
          <a className="rounded-2xl border border-white/10 px-5 py-3 text-sm text-slate-200 transition hover:border-cyan-200/40 hover:text-cyan-100" href="/dashboard">回到仪表盘</a>
        </div>
      </section>
    </main>
  );
}
