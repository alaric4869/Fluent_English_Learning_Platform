"use client";

import { useEffect, useState } from "react";

export function IeltsTimer({ minutes }: { minutes: number }) {
  const [seconds, setSeconds] = useState(minutes * 60);
  const [running, setRunning] = useState(false);

  useEffect(() => {
    if (!running || seconds <= 0) return;
    const timer = window.setInterval(() => setSeconds((value) => Math.max(0, value - 1)), 1000);
    return () => window.clearInterval(timer);
  }, [running, seconds]);

  const display = `${String(Math.floor(seconds / 60)).padStart(2, "0")}:${String(seconds % 60).padStart(2, "0")}`;
  return (
    <div className={`ielts-timer ${seconds === 0 ? "finished" : ""}`}>
      <div><span>考试计时</span><strong>{display}</strong></div>
      <button onClick={() => setRunning((value) => !value)}>{running ? "暂停" : seconds === minutes * 60 ? "开始计时" : "继续"}</button>
      <button className="timer-reset" onClick={() => { setSeconds(minutes * 60); setRunning(false); }}>重置</button>
    </div>
  );
}
