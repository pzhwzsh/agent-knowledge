"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiRequest, UserFeedback } from "../../../lib/api";
import { useAuth } from "../../../lib/auth";
import { AppShell, EmptyState, PageCard } from "../../../components/AppShell";

const statuses = ["open", "planned", "in_progress", "resolved", "wont_fix", "deleted"] as const;
type FeedbackStatus = (typeof statuses)[number];

export default function AdminFeedbackPage() {
  const router = useRouter();
  const auth = useAuth();
  const queryClient = useQueryClient();
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [notice, setNotice] = useState("");

  useEffect(() => {
    if (!auth.isLoading && !auth.token) router.push("/");
    if (!auth.isLoading && auth.user && !auth.user.is_admin) router.push("/dashboard");
  }, [auth.isLoading, auth.token, auth.user, router]);

  const feedbackQuery = useQuery({
    queryKey: ["admin-feedback", auth.token, statusFilter],
    enabled: Boolean(auth.token && auth.user?.is_admin),
    queryFn: () => apiRequest<UserFeedback[]>(`/api/feedback/admin/all${statusFilter ? `?status=${statusFilter}` : ""}`, {}, auth.token),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: FeedbackStatus }) =>
      apiRequest<UserFeedback>(`/api/feedback/admin/${id}`, { method: "PATCH", body: JSON.stringify({ status }) }, auth.token),
    onSuccess: async () => {
      setNotice("反馈状态已更新，并写入审计日志。");
      await queryClient.invalidateQueries({ queryKey: ["admin-feedback", auth.token] });
    },
    onError: (error) => setNotice(error instanceof Error ? error.message : "更新失败"),
  });

  const items = feedbackQuery.data ?? [];
  return (
    <AppShell user={auth.user} onSignOut={() => { auth.signOut(); router.push("/"); }}>
      <PageCard>
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-sm text-cyan-100/70">Admin</p>
            <h1 className="mt-2 text-3xl font-semibold">反馈处理后台</h1>
            <p className="mt-2 text-sm text-slate-400">查看用户提交的问题、维修建议和删除建议，并标记处理状态。</p>
          </div>
          <label className="min-w-48 text-sm text-slate-300">
            状态筛选
            <select className="mt-2 w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-sm outline-none" value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
              <option value="">全部</option>
              {statuses.map((status) => <option key={status} value={status}>{status}</option>)}
            </select>
          </label>
        </div>
        {notice ? <p className="mt-4 rounded-2xl border border-white/10 bg-white/[0.06] p-3 text-sm">{notice}</p> : null}
        <div className="mt-6 space-y-3">
          {feedbackQuery.isLoading ? <EmptyState text="正在加载用户反馈..." /> : null}
          {items.map((item) => (
            <article className="rounded-3xl border border-white/10 bg-slate-950/35 p-5" key={item.id}>
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h2 className="text-lg font-semibold">{item.feature}</h2>
                  <p className="mt-1 text-xs text-slate-500">用户 {item.user_id} · {new Date(item.created_at).toLocaleString()}</p>
                </div>
                <span className="rounded-full bg-white/10 px-3 py-1 text-xs">{item.feedback_type} · {item.severity} · {item.status}</span>
              </div>
              <p className="mt-4 text-sm leading-6 text-slate-300">{item.message}</p>
              <div className="mt-4 flex flex-wrap gap-2">
                {statuses.map((status) => (
                  <button className="rounded-full border border-white/10 px-3 py-1.5 text-xs text-slate-300 transition hover:border-cyan-200/50 hover:text-cyan-100 disabled:opacity-40" disabled={updateMutation.isPending || item.status === status} key={status} type="button" onClick={() => updateMutation.mutate({ id: item.id, status })}>
                    {status}
                  </button>
                ))}
              </div>
            </article>
          ))}
          {!feedbackQuery.isLoading && items.length === 0 ? <EmptyState text="当前没有符合条件的反馈。" /> : null}
        </div>
      </PageCard>
    </AppShell>
  );
}
