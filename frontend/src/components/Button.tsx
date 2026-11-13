import type { ButtonHTMLAttributes } from "react";

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "default" | "danger" | "ghost";
  size?: "sm" | "md";
  block?: boolean;
};

export default function Button({ variant = "default", size = "md", block, className = "", type = "button", ...rest }: Props) {
  const cls = ["btn", variant !== "default" && `btn-${variant}`, size === "sm" && "btn-sm", block && "btn-block", className]
    .filter(Boolean)
    .join(" ");
  return <button type={type} className={cls} {...rest} />;
}
