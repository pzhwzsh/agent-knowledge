"use client";

import { ReactNode, useEffect } from "react";
import { SkeletonCard } from "./AppShell";
import { useToast } from "./ToastProvider";

export function useQueryErrorToast({ error, fallbackMessage, isError }: { error: unknown; fallbackMessage: string; isError: boolean }) {
  const { notify } = useToast();

  useEffect(() => {
    if (!isError) return;
    notify(error instanceof Error ? error.message : fallbackMessage, "error");
  }, [error, fallbackMessage, isError, notify]);
}

export function SkeletonList({ className = "", count, renderItem }: { className?: string; count: number; renderItem?: (index: number) => ReactNode }) {
  return <div className={className}>{Array.from({ length: count }, (_, index) => renderItem ? renderItem(index) : <SkeletonCard key={index} />)}</div>;
}
