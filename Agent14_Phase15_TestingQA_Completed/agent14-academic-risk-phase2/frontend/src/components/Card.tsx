import type { CSSProperties, ReactNode } from "react";

interface CardProps {
  children: ReactNode;
  className?: string;
  as?: "div" | "section" | "article";
  id?: string;
  style?: CSSProperties;
}

export default function Card({ children, className = "", as = "div", id, style }: CardProps) {
  const Tag = as;
  return (
    <Tag id={id} style={style} className={`u8-no-overflow min-w-0 rounded-[var(--radius-card)] border border-slate-200 bg-white shadow-[var(--shadow-card)] ${className}`}>
      {children}
    </Tag>
  );
}
