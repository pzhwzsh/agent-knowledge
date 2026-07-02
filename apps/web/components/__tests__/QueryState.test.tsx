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

  it("shows query errors through the toast provider", async () => {
    render(
      <ToastProvider>
        <ErrorToastProbe error={new Error("Query failed")} isError />
      </ToastProvider>,
    );

    expect(await screen.findByText("Query failed")).toBeInTheDocument();
  });
});
