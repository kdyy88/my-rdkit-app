"use client";
import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { API_BASE } from '../src/config';

export default function SimilarityChecker() {
  const [smi1, setSmi1] = useState("CC(=O)Oc1ccccc1C(=O)O"); // 阿司匹林
  const [smi2, setSmi2] = useState("CC(=O)Nc1ccc(O)cc1");    // 对乙酰氨基酚
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const checkSimilarity = async () => {
    if (!smi1 || !smi2) return;
    setLoading(true);
    
    try {
      // 2. 使用统一的 API_BASE 拼接
      const res = await fetch(`${API_BASE}/similarity?smi1=${encodeURIComponent(smi1)}&smi2=${encodeURIComponent(smi2)}`);
      
      if (!res.ok) throw new Error("后端连接失败");
      
      const json = await res.json();
      setData(json);
    } catch (error) {
      console.error("相似度计算出错:", error);
      alert("计算失败，请检查后端服务");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="w-full max-w-2xl mx-auto mt-6">
      <CardHeader><CardTitle>分子相似度对比</CardTitle></CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <Input 
            value={smi1} 
            onChange={(e)=>setSmi1(e.target.value)} 
            placeholder="输入第一个 SMILES..." 
          />
          <Input 
            value={smi2} 
            onChange={(e)=>setSmi2(e.target.value)} 
            placeholder="输入第二个 SMILES..." 
          />
        </div>
        <Button 
          className="w-full" 
          onClick={checkSimilarity} 
          disabled={loading}
        >
          {loading ? "计算中..." : "计算 Tanimoto 相似度"}
        </Button>
        
        {data && (
          <div className="pt-4 space-y-2">
            <div className="flex justify-between items-center text-sm font-medium">
              {/* 优化显示：如果是数字，保留两位小数 */}
              <span>相似度得分: {typeof data.score === 'number' ? data.score.toFixed(3) : data.score}</span>
              <Badge variant={data.score > 0.7 ? "default" : "secondary"}>
                {data.status}
              </Badge>
            </div>
            <Progress value={(data.score || 0) * 100} className="h-2" />
            <p className="text-center text-xs text-gray-500">基于 Morgan Fingerprint (Radius 2)</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}