"use client";

import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiRequest, AuditLog } from "../../../lib/api";
import { useAuth } from "../../../lib/auth";
import { AppShell, EmptyState, PageCard } from "../../../components/AppShell";
import { SkeletonList, useQueryErrorToast } from "../../../components/QueryState";

export default function AdminAuditPage() {
  const router = useRouter();
  const auth = useAuth();
  const [action, setAction] = useState("");
  const [resourceType, setResourceType] = useState("");

  useEffect(() => {
    if (!auth.isLoading && !auth.token) router.push("/");
    if (!auth.isLoading && auth.user && !auth.user.is_admin) router.push("/dashboard");
  }, [auth.isLoading, auth.token, auth.user, router]);

  const query = useQuery({
    queryKey: ["admin-audit", auth.token, action, resourceType],
    enabled: Boolean(auth.token && auth.user?.is_admin),
    queryFn: () => {
      const params = new URLSearchParams();
      if (action.trim()) params.set("action", action.trim());
      if (resourceType.trim()) params.set("resource_type", resourceType.trim());
      const queryString = params.toString();
      return apiRequest<AuditLog[]>(`/api/audit/logs${queryString ? `?${queryString}` : ""}`, {}, auth.token);
    },
  });

  useQueryErrorToast({ error: query.error, fallbackMessage: "Failed to load audit logs", isError: query.isError });

  const logs = query.data ?? [];
  return (
    <AppShell user={auth.user} onSignOut={() => { auth.signOut(); router.push("/"); }}>
      <PageCard>
        <div>
          <p className="text-sm text-cyan-100/70">Admin</p>
          <h1 className="mt-2 text-3xl font-semibold">审计日志</h1>
          <p className="mt-2 text-sm text-slate-400">查看管理员操作和敏感接口访问记录，后续排查问题和追责用。</p>
        </div>
        <div className="mt-6 grid gap-4 rounded-3xl border border-white/10 bg-slate-950/35 p-5 md:grid-cols-2">
          <label className="text-sm text-slate-300">
            Action 筛选
            <input className="mt-2 w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-sm outline-none" value={action} onChange={(event) => setAction(event.target.value)} placeholder="例如 feedback_status_update" />
          </label>
          <label className="text-sm text-slate-300">
            Resource Type 筛选
            <input className="mt-2 w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-sm outline-none" value={resourceType} onChange={(event) => setResourceType(event.target.value)} placeholder="例如 user_feedback" />
          </label>
        </div>
        <div className="mt-6 space-y-3">
          {query.isLoading ? <SkeletonList className="space-y-3" count={3} /> : null}
          {query.isError ? <EmptyState text="审计日志加载失败，请确认当前账号有管理员权限。" /> : null}
          {logs.map((log) => (
            <article className="rounded-3xl border border-white/10 bg-slate-950/35 p-5" key={log.id}>
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h2 className="text-lg font-semibold">{log.action}</h2>
                  <p className="mt-1 text-xs text-slate-500">操作者 {log.user_id} · {new Date(log.created_at).toLocaleString()}</p>
                </div>
                <span className="rounded-full bg-white/10 px-3 py-1 text-xs">{log.resource_type ?? "无资源"}</span>
              </div>
              {log.resource_id ? <p className="mt-3 text-xs text-slate-500">资源 ID：{log.resource_id}</p> : null}
              <pre className="mt-4 overflow-auto rounded-2xl border border-white/10 bg-black/30 p-3 text-xs leading-5 text-slate-300">{JSON.stringify(log.metadata_json, null, 2)}</pre>
            </article>
          ))}
          {query.isLoading ? <SkeletonList className="space-y-3" count={3} /> : null}
        </div>
      </PageCard>
    </AppShell>
  );
}
