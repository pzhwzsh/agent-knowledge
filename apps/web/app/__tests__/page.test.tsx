import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import Home from "../page";

const pushMock = vi.fn();
const notifyMock = vi.fn();
const apiRequestMock = vi.fn();
const storeTokenMock = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock }),
}));

vi.mock("../../components/ToastProvider", () => ({
  useToast: () => ({ notify: notifyMock }),
}));

vi.mock("../../lib/api", () => ({
  apiRequest: (...args: unknown[]) => apiRequestMock(...args),
}));

vi.mock("../../lib/auth", () => ({
  storeToken: (token: string) => storeTokenMock(token),
}));

const emailLabel = "邮箱";
const passwordLabel = "密码";
const displayNameLabel = "昵称";
const loginButton = "进入个人雷达";
const registerTab = "注册";
const registerButton = "创建并登录";

describe("Home auth page", () => {
  beforeEach(() => {
    pushMock.mockReset();
    notifyMock.mockReset();
    apiRequestMock.mockReset();
    storeTokenMock.mockReset();
  });

  it("logs in and routes to the dashboard", async () => {
    apiRequestMock.mockResolvedValueOnce({ access_token: "login-token", token_type: "bearer" });

    render(<Home />);
    fireEvent.change(screen.getByLabelText(emailLabel), { target: { value: "user@example.com" } });
    fireEvent.change(screen.getByLabelText(passwordLabel), { target: { value: "password123" } });
    fireEvent.click(screen.getByRole("button", { name: loginButton }));

    await waitFor(() => expect(pushMock).toHaveBeenCalledWith("/dashboard"));
    expect(apiRequestMock).toHaveBeenCalledWith(
      "/api/auth/login",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ email: "user@example.com", password: "password123" }),
      }),
      null,
    );
    expect(storeTokenMock).toHaveBeenCalledWith("login-token");
    expect(notifyMock).toHaveBeenCalledWith("登录成功。", "success");
  });

  it("registers a user, logs in, and routes to the dashboard", async () => {
    apiRequestMock
      .mockResolvedValueOnce({ id: "user-id", email: "new@example.com", display_name: "New User" })
      .mockResolvedValueOnce({ access_token: "register-token", token_type: "bearer" });

    render(<Home />);
    fireEvent.click(screen.getByRole("button", { name: registerTab }));
    fireEvent.change(screen.getByLabelText(displayNameLabel), { target: { value: "New User" } });
    fireEvent.change(screen.getByLabelText(emailLabel), { target: { value: "new@example.com" } });
    fireEvent.change(screen.getByLabelText(passwordLabel), { target: { value: "password123" } });
    fireEvent.click(screen.getByRole("button", { name: registerButton }));

    await waitFor(() => expect(pushMock).toHaveBeenCalledWith("/dashboard"));
    expect(apiRequestMock).toHaveBeenNthCalledWith(
      1,
      "/api/auth/register",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ email: "new@example.com", password: "password123", display_name: "New User" }),
      }),
      null,
    );
    expect(apiRequestMock).toHaveBeenNthCalledWith(
      2,
      "/api/auth/login",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ email: "new@example.com", password: "password123" }),
      }),
      null,
    );
    expect(storeTokenMock).toHaveBeenCalledWith("register-token");
    expect(notifyMock).toHaveBeenCalledWith("注册成功，已进入工作台。", "success");
  });

  it("shows an error toast when authentication fails", async () => {
    apiRequestMock.mockRejectedValueOnce(new Error("Invalid credentials"));

    render(<Home />);
    fireEvent.change(screen.getByLabelText(emailLabel), { target: { value: "user@example.com" } });
    fireEvent.change(screen.getByLabelText(passwordLabel), { target: { value: "password123" } });
    fireEvent.click(screen.getByRole("button", { name: loginButton }));

    await waitFor(() => expect(notifyMock).toHaveBeenCalledWith("Invalid credentials", "error"));
    expect(storeTokenMock).not.toHaveBeenCalled();
    expect(pushMock).not.toHaveBeenCalled();
  });
});
