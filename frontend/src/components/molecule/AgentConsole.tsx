"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import MoleculeCard from "@/components/molecule/MoleculeCard";
import type { ChatResponse, MoleculeResponse } from "@/lib/types";

export default function AgentConsole() {
  const [message, setMessage] = useState("请分析 CCO 的性质并简明解释");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<MoleculeResponse | null>(null);

  const onSubmit = async () => {
    if (!message.trim()) return;
    setLoading(true);
    setError(null);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message, max_turns: 3 }),
      });

      const data = (await res.json()) as ChatResponse | { error?: string; details?: string };
      if (!res.ok || !("result" in data)) {
        throw new Error((data as { error?: string }).error || "请求失败");
      }

      setResult(data.result);
    } catch (e) {
      setError(e instanceof Error ? e.message : "未知错误");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="w-full max-w-4xl mx-auto shadow-xl">
      <CardHeader>
        <CardTitle>AG2 + MCP 化学 Agent</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex gap-2">
          <Input value={message} onChange={(e) => setMessage(e.target.value)} placeholder="输入化合物名称或 SMILES" />
          <Button onClick={onSubmit} disabled={loading}>{loading ? "分析中..." : "开始分析"}</Button>
        </div>

        {error && <p className="text-sm text-red-600">{error}</p>}
        {loading && <MoleculeCard loading />}
        {!loading && result && <MoleculeCard result={result} />}
      </CardContent>
    </Card>
  );
}
