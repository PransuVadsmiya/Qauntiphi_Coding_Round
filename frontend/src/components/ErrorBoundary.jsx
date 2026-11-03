import { Component } from "react";

/** Keeps a crash in one widget from blanking the whole page. */
export default class ErrorBoundary extends Component {
  state = { error: null };

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidCatch(error, info) {
    console.error(`[${this.props.name || "widget"}]`, error, info?.componentStack);
  }

  render() {
    if (this.state.error) {
      return (
        <div className="card alert-soft">
          <strong>{this.props.name || "This section"} failed to load.</strong>
          <span className="muted small"> {String(this.state.error.message || this.state.error)}</span>
          <button className="ghost" onClick={() => this.setState({ error: null })}>Try again</button>
        </div>
      );
    }
    return this.props.children;
  }
}
