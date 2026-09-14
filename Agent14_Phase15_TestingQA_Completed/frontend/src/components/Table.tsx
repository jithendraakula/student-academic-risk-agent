import type { ReactNode } from "react";

export interface TableColumn<T> {
  key: string;
  header: string;
  render: (row: T) => ReactNode;
  className?: string;
}

interface TableProps<T> {
  columns: TableColumn<T>[];
  rows: T[];
  rowKey: (row: T, index: number) => string;
  caption?: string;
  emptyMessage?: string;
}

export default function Table<T>({ columns, rows, rowKey, caption, emptyMessage = "No records to display." }: TableProps<T>) {
  return (
    <div className="ui-table-shell overflow-hidden rounded-xl border border-slate-200 bg-white">
      <div className="flex items-center justify-between gap-3 border-b border-slate-100 px-4 py-2 md:hidden">
        <span className="text-[10px] font-semibold uppercase tracking-[0.12em] text-slate-400">More columns</span>
        <span className="text-[10px] font-medium text-slate-400">Swipe to see more</span>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-[760px] border-collapse text-left text-sm lg:min-w-full">
          {caption ? <caption className="sr-only">{caption}</caption> : null}
          <thead className="bg-[#f5f8fc] text-[10px] font-bold uppercase tracking-[0.13em] text-[#617188]">
            <tr>
              {columns.map((column) => (
                <th key={column.key} scope="col" className={`whitespace-nowrap border-b border-slate-200 px-4 py-3 ${column.className ?? ""}`}>
                  {column.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {rows.length > 0 ? rows.map((row, index) => (
              <tr key={rowKey(row, index)} className="transition-colors hover:bg-[#f7fbff]">
                {columns.map((column) => (
                  <td key={column.key} className={`break-words px-4 py-3.5 align-middle text-[#364a63] ${column.className ?? ""}`}>
                    {column.render(row)}
                  </td>
                ))}
              </tr>
            )) : (
              <tr>
                <td colSpan={columns.length} className="px-4 py-12 text-center text-sm text-slate-500">{emptyMessage}</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
