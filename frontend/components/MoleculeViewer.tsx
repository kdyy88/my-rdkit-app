"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button"; // 记得 add button

export default function MoleculeViewer() {
  const [smiles, setSmiles] = useState("c1ccccc1");
  const [svg, setSvg] = useState("");
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  // 前端实时预览
  useEffect(() => {
    const render = async () => {
      if (typeof window !== "undefined" && (window as any).initRDKitModule) {
        const rdkit = await (window as any).initRDKitModule();
        const mol = rdkit.get_mol(smiles);
        if (mol) {
          setSvg(mol.get_svg());
          mol.delete();
        }
      }
    };
    render();
  }, [smiles]);

  // 调用后端 API
  const handleAnalyze = async () => {
    setLoading(true);
    try {
      const response = await fetch(`http://127.0.0.1:8000/calc?smiles=${encodeURIComponent(smiles)}`);
      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error("后端连接失败", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="w-full max-w-2xl mx-auto shadow-xl">
      <CardHeader>
        <CardTitle>化学性质分析终端</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="flex gap-2">
          <Input 
            value={smiles} 
            onChange={(e) => setSmiles(e.target.value)}
            placeholder="输入 SMILES..."
          />
          <Button onClick={handleAnalyze} disabled={loading}>
            {loading ? "计算中..." : "后端分析"}
          </Button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* 左侧：结构展示 */}
          <div className="border rounded-lg p-4 bg-white flex justify-center items-center h-64">
             <div dangerouslySetInnerHTML={{ __html: svg }} className="w-full h-full" />
          </div>

          {/* 右侧：后端数据 */}
          <div className="bg-slate-50 rounded-lg p-4 space-y-3 text-sm">
            <h3 className="font-bold text-slate-700 border-b pb-2">计算结果 (RDKit Python)</h3>
            {result ? (
              <>
                <div className="flex justify-between"><span>分子量:</span> <b>{result.mw}</b></div>
                <div className="flex justify-between"><span>LogP:</span> <b>{result.logp}</b></div>
                <div className="flex justify-between"><span>氢键供体:</span> <b>{result.hbd}</b></div>
                <div className="flex justify-between"><span>氢键受体:</span> <b>{result.hba}</b></div>
              </>
            ) : (
              <p className="text-gray-400 italic">点击按钮开始分析...</p>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}