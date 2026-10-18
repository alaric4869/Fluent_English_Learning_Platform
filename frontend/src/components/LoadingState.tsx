export function LoadingState() {
  return (
    <div className="loading-state" aria-live="polite">
      <span />
      <h2>Preparing your study day</h2>
      <p>Selecting fresh material and due reviews…</p>
    </div>
  );
}


export function ErrorState({ message }: { message: string }) {
  return (
    <div className="error-state" role="alert">
      <strong>无法连接学习数据</strong>
      <p>{message}</p>
      <p>请确认 FastAPI 正在 http://127.0.0.1:8000 运行。</p>
    </div>
  );
}
