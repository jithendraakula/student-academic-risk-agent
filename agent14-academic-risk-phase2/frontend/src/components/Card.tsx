import type { ReactNode } from "react";

interface CardProps {
  children: ReactNode;
  className?: string;
  as?: "div" | "section" | "article";
}

export default function Card({ children, className = "", as = "div" }: CardProps) {
  const Tag = as;
  return (
    <Tag className={`bg-white rounded-[var(--radius-card)] border border-slate-200/80 shadow-[var(--shadow-card)] p-5 ${className}`}>
      {children}
    </Tag>
  );
}
