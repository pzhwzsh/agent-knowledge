import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { SkeletonList, useQueryErrorToast } from "../QueryState";
import { ToastProvider } from "../ToastProvider";

function ErrorToastProbe({ error, isError }: { error: unknown; isError: boolean }) {
  useQueryErrorToast({ error, fallbackMessage: "Fallback error", isError });
  return <div>probe</div>;
}

describe("QueryState", () => {
  it("renders a configurable skeleton list", () => {
    render(<SkeletonList count={3} />);

    expect(document.querySelectorAll(".animate-pulse")).toHaveLength(12);
  });

  it("uses a custom skeleton item renderer when provided", () => {
    render(<SkeletonList count={2} renderItem={(index) => <span key={index}>Row {index + 1}</span>} />);

    expect(screen.getByText("Row 1")).toBeInTheDocument();
    expect(screen.getByText("Row 2")).toBeInTheDocument();
  });

  it("shows query errors through the toast provider", async () => {
    render(
      <ToastProvider>
        <ErrorToastProbe error={new Error("Query failed")} isError />
      </ToastProvider>,
    );

    expect(await screen.findByText("Query failed")).toBeInTheDocument();
  });

  it("uses the fallback query error message for non-Error values", async () => {
    render(
      <ToastProvider>
        <ErrorToastProbe error={{ detail: "unknown" }} isError />
      </ToastProvider>,
    );

    expect(await screen.findByText("Fallback error")).toBeInTheDocument();
  });
});
