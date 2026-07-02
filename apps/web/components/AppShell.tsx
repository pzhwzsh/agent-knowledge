"use client";

import Link from "next/link";
import { ReactNode } from "react";
import { User } from "../lib/api";

const navItems = [
  { href: "/dashboard", label: "仪表盘" },
  { href: "/documents", label: "文档" },
  { href: "/recommendations", label: "推荐" },
  { href: "/search", label: "搜索问答" },
  { href: "/preferences", label: "偏好" },
  { href: "/feedback", label: "反馈维修" },
];

const adminNavItems = [
  { href: "/admin/feedback", label: "反馈处理" },
  { href: "/admin/audit", label: "审计日志" },
];

export function AppShell({ children, user, onSignOut }: { children: ReactNode; user: User | null; onSignOut: () => void }) {
  const displayName = user?.display_name || user?.email || "未登录";
  const visibleNavItems = user?.is_admin ? [...navItems, ...adminNavItems] : navItems;
  return (
    <main className="min-h-screen bg-[#08111f] text-slate-100">
      <div className="fixed inset-0 -z-10 bg-[radial-gradient(circle_at_20%_20%,rgba(56,189,248,0.18),transparent_32%),radial-gradient(circle_at_82%_12%,rgba(168,85,247,0.18),transparent_30%)]" />
      <div className="mx-auto flex w-full max-w-7xl gap-5 px-5 py-5 lg:px-8">
        <aside className="sticky top-5 hidden h-[calc(100vh-2.5rem)] w-64 shrink-0 rounded-[2rem] border border-white/10 bg-white/[0.07] p-5 backdrop-blur-2xl lg:block">
          <Link className="flex items-center gap-3" href="/dashboard">
            <span className="grid h-11 w-11 place-items-center rounded-2xl border border-cyan-200/30 bg-cyan-200/15">
              <span className="h-4 w-4 rounded-full bg-cyan-200 shadow-[0_0_24px_rgba(103,232,249,0.9)]" />
            </span>
            <span>
              <span className="block text-sm text-cyan-100/70">Personal Radar</span>
              <span className="font-semibold">个人信息雷达</span>
            </span>
          </Link>
          <nav className="mt-8 space-y-2">
            {visibleNavItems.map((item) => (
              <Link className="block rounded-2xl border border-transparent px-4 py-3 text-sm text-slate-300 transition hover:border-white/10 hover:bg-white/[0.07] hover:text-white" href={item.href} key={item.href}>{item.label}</Link>
            ))}
          </nav>
          <div className="absolute inset-x-5 bottom-5 rounded-3xl border border-white/10 bg-slate-950/45 p-4">
            <p className="text-xs text-slate-500">当前用户</p>
            <p className="mt-1 truncate text-sm font-medium">{displayName}</p>
            <button className="mt-3 rounded-full border border-white/10 px-3 py-1.5 text-xs text-slate-300 transition hover:border-rose-200/40 hover:text-rose-100" type="button" onClick={onSignOut}>退出登录</button>
          </div>
        </aside>
        <section className="min-w-0 flex-1">
          <div className="mb-5 flex flex-wrap items-center justify-between gap-3 rounded-[1.5rem] border border-white/10 bg-white/[0.07] p-3 backdrop-blur-2xl lg:hidden">
            <Link className="font-semibold" href="/dashboard">个人信息雷达</Link>
            <div className="flex flex-wrap gap-2 text-xs">
              {visibleNavItems.map((item) => <Link className="rounded-full bg-white/10 px-3 py-1.5" href={item.href} key={item.href}>{item.label}</Link>)}
            </div>
          </div>
          {children}
        </section>
      </div>
    </main>
  );
}

export function PageCard({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <section className={`rounded-[2rem] border border-white/10 bg-white/[0.07] p-5 shadow-2xl shadow-slate-950/30 backdrop-blur-2xl sm:p-6 ${className}`}>{children}</section>;
}

export function EmptyState({ text }: { text: string }) {
  return <div className="rounded-2xl border border-dashed border-white/10 bg-slate-950/35 p-5 text-sm text-slate-400">{text}</div>;
}
