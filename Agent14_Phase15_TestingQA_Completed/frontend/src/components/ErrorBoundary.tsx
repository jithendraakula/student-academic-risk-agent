import React from "react";
import Card from "./Card";

interface Props { children: React.ReactNode }
interface State { failed: boolean }

export default class ErrorBoundary extends React.Component<Props, State> {
  state: State = { failed: false };
  static getDerivedStateFromError(): State { return { failed: true }; }
  componentDidCatch(error: Error) { console.error("Academic risk UI error", error); }
  render() {
    if (!this.state.failed) return this.props.children;
    return <div className="mx-auto max-w-3xl p-6"><Card as="section" className="p-6"><p className="ui-eyebrow">Workspace error</p><h1 className="mt-1 text-xl font-bold text-ink-900">This page could not finish rendering</h1><p className="mt-2 text-sm leading-6 text-slate-600">Your data is safe. Reload the page to recover the workspace.</p><button type="button" className="ui-button ui-button-primary mt-4" onClick={() => window.location.reload()}>Reload workspace</button></Card></div>;
  }
}
