import type { ReactNode } from "react";

interface CardProps {
  children: ReactNode;
  className?: string;
  as?: "div" | "section" | "article";
}

export default function Card({ children, className = "", as = "div" }: CardProps) {
  const Tag = as;
  return (
    <Tag className={`bg-white rounded-2xl border border-slate-200 shadow-sm p-5 ${className}`}>
      {children}
    </Tag>
  );
}
