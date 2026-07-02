import { afterEach, describe, expect, it, vi } from "vitest";
import { API_UNAUTHORIZED_EVENT, ApiError, apiRequest } from "../api";

describe("apiRequest", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  it("sends JSON headers and bearer token, then returns JSON", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ ok: true }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await expect(
      apiRequest<{ ok: boolean }>("/api/example", { method: "POST" }, "token-123"),
    ).resolves.toEqual({ ok: true });

    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/api/example",
      expect.objectContaining({
        method: "POST",
        headers: expect.objectContaining({
          "Content-Type": "application/json",
          Authorization: "Bearer token-123",
        }),
      }),
    );
  });

  it("uses backend string detail as the ApiError message", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ detail: "Invalid credentials" }), {
          status: 400,
          headers: { "Content-Type": "application/json" },
        }),
      ),
    );

    await expect(apiRequest("/api/auth/login")).rejects.toMatchObject({
      name: "ApiError",
      message: "Invalid credentials",
      status: 400,
      path: "/api/auth/login",
    });
  });

  it("dispatches the unauthorized event on 401 responses", async () => {
    const listener = vi.fn();
    window.addEventListener(API_UNAUTHORIZED_EVENT, listener);
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ detail: "Token expired" }), {
          status: 401,
          headers: { "Content-Type": "application/json" },
        }),
      ),
    );

    await expect(apiRequest("/api/auth/me")).rejects.toBeInstanceOf(ApiError);
    expect(listener).toHaveBeenCalledTimes(1);
    window.removeEventListener(API_UNAUTHORIZED_EVENT, listener);
  });

  it("converts request timeout aborts to ApiError", async () => {
    vi.useFakeTimers();
    vi.stubGlobal(
      "fetch",
      vi.fn((_url: string, init?: RequestInit) => {
        return new Promise((_resolve, reject) => {
          init?.signal?.addEventListener("abort", () => reject(new DOMException("Aborted", "AbortError")));
        });
      }),
    );

    const requestExpectation = expect(apiRequest("/api/slow", { timeoutMs: 50 })).rejects.toMatchObject({
      name: "ApiError",
      message: "请求超时，请稍后重试",
      status: 0,
      path: "/api/slow",
    });

    await vi.advanceTimersByTimeAsync(50);
    await requestExpectation;
  });
});
