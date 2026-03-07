"use client";
import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";

export default function SimilarityChecker() {
  const [smi1, setSmi1] = useState("CC(=O)Oc1ccccc1C(=O)O"); // 阿司匹林
  const [smi2, setSmi2] = useState("CC(=O)Nc1ccc(O)cc1");    // 对乙酰氨基酚
  const [data, setData] = useState<any>(null);

  const checkSimilarity = async () => {
    const res = await fetch(`http://127.0.0.1:8000/similarity?smi1=${encodeURIComponent(smi1)}&smi2=${encodeURIComponent(smi2)}`);
    const json = await res.json();
    setData(json);
  };

  return (
    <Card className="w-full max-w-2xl mx-auto mt-6">
      <CardHeader><CardTitle>分子相似度对比</CardTitle></CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <Input value={smi1} onChange={(e)=>setSmi1(e.target.value)} placeholder="SMILES A" />
          <Input value={smi2} onChange={(e)=>setSmi2(e.target.value)} placeholder="SMILES B" />
        </div>
        <Button className="w-full" onClick={checkSimilarity}>计算 Tanimoto 相似度</Button>
        
        {data && (
          <div className="pt-4 space-y-2">
            <div className="flex justify-between items-center text-sm font-medium">
              <span>相似度得分: {data.score}</span>
              <Badge variant={data.score > 0.7 ? "default" : "secondary"}>{data.status}</Badge>
            </div>
            <Progress value={data.score * 100} className="h-2" />
            <p className="text-center text-xs text-gray-500">基于 Morgan Fingerprint (Radius 2)</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}