import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ToastProvider, useToast } from "../ToastProvider";

function ToastProbe() {
  const { notify } = useToast();
  return (
    <div>
      <button type="button" onClick={() => notify("Saved", "success")}>Show success</button>
      <button type="button" onClick={() => notify("Failed", "error")}>Show error</button>
      <button type="button" onClick={() => notify("Heads up")}>Show info</button>
    </div>
  );
}

describe("ToastProvider", () => {
  afterEach(() => {
    vi.useRealTimers();
  });

  it("renders success, error, and info toasts with their visual classes", () => {
    render(
      <ToastProvider>
        <ToastProbe />
      </ToastProvider>,
    );

    fireEvent.click(screen.getByRole("button", { name: "Show success" }));
    fireEvent.click(screen.getByRole("button", { name: "Show error" }));
    fireEvent.click(screen.getByRole("button", { name: "Show info" }));

    expect(screen.getByRole("button", { name: "Saved" })).toHaveClass("bg-emerald-500/15");
    expect(screen.getByRole("button", { name: "Failed" })).toHaveClass("bg-rose-500/15");
    expect(screen.getByRole("button", { name: "Heads up" })).toHaveClass("bg-cyan-500/15");
  });

  it("dismisses a toast when it is clicked", async () => {
    render(
      <ToastProvider>
        <ToastProbe />
      </ToastProvider>,
    );

    fireEvent.click(screen.getByRole("button", { name: "Show success" }));
    fireEvent.click(screen.getByRole("button", { name: "Saved" }));

    await waitFor(() => expect(screen.queryByRole("button", { name: "Saved" })).not.toBeInTheDocument());
  });

  it("auto dismisses toasts after the timeout", async () => {
    vi.useFakeTimers();
    render(
      <ToastProvider>
        <ToastProbe />
      </ToastProvider>,
    );

    fireEvent.click(screen.getByRole("button", { name: "Show info" }));
    expect(screen.getByRole("button", { name: "Heads up" })).toBeInTheDocument();

    await act(async () => {
      await vi.advanceTimersByTimeAsync(4500);
    });

    expect(screen.queryByRole("button", { name: "Heads up" })).not.toBeInTheDocument();
  });
});
