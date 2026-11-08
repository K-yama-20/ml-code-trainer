import { render, screen } from "@testing-library/react";
import { expect, it } from "vitest";
import { Button, ErrorBox } from "./ui";
it("exposes disabled controls to assistive technology", () => {
  render(<Button disabled>実行</Button>);
  expect(screen.getByRole("button", { name: "実行" })).toBeDisabled();
});
it("announces a system error without discarding the editor", () => {
  render(<ErrorBox error={new Error("ネットワークに接続できません")} />);
  expect(screen.getByRole("alert")).toHaveTextContent(
    "ネットワークに接続できません",
  );
});
