import type { ReactNode } from "react";

interface CardProps {
  children: ReactNode;
  className?: string;
  as?: "div" | "section" | "article";
}

export default function Card({ children, className = "", as = "div" }: CardProps) {
  const Tag = as;
  return (
    <Tag className={`rounded-[var(--radius-card)] border border-slate-200 bg-white shadow-[var(--shadow-card)] transition-shadow duration-150 ${className}`}>
      {children}
    </Tag>
  );
}