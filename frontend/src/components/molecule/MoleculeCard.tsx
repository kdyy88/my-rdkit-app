"use client";

import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import type { MoleculeResponse } from "@/lib/types";

type Props = {
  result?: MoleculeResponse | null;
  loading?: boolean;
};

function normalizeImage(image?: string | null): string | null {
  if (!image) return null;
  if (image.startsWith("data:image")) return image;
  return `data:image/png;base64,${image}`;
}

export default function MoleculeCard({ result, loading = false }: Props) {
  const [copied, setCopied] = useState(false);

  if (loading) {
    return (
      <Card className="w-full shadow-lg">
        <CardHeader className="space-y-2">
          <Skeleton className="h-6 w-2/3" />
          <Skeleton className="h-4 w-full" />
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-2">
          <Skeleton className="h-56 w-full" />
          <div className="space-y-2">
            <Skeleton className="h-5 w-full" />
            <Skeleton className="h-5 w-full" />
            <Skeleton className="h-5 w-full" />
            <Skeleton className="h-5 w-full" />
            <Skeleton className="h-5 w-full" />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!result) return null;

  const imageSrc = normalizeImage(result.visualization?.image_base64);
  const p = result.properties;

  const onCopySmiles = async () => {
    if (!result.smiles) return;
    await navigator.clipboard.writeText(result.smiles);
    setCopied(true);
    setTimeout(() => setCopied(false), 1200);
  };

  return (
    <Card className="w-full shadow-lg">
      <CardHeader className="space-y-2">
        <CardTitle className="flex items-center justify-between gap-2">
          <span>{result.compound_name || "Molecule Analysis"}</span>
          <div className="flex items-center gap-2">
            <Badge variant="secondary">{result.smiles || "N/A"}</Badge>
            <Button variant="outline" size="sm" onClick={onCopySmiles}>
              {copied ? "已复制" : "复制 SMILES"}
            </Button>
          </div>
        </CardTitle>
        <p className="text-sm text-slate-600">{result.summary}</p>
      </CardHeader>

      <CardContent className="grid gap-4 md:grid-cols-2">
        <div className="rounded-md border bg-white p-2 min-h-56 flex items-center justify-center">
          {imageSrc ? (
            <img src={imageSrc} alt={result.smiles} className="max-h-56 w-auto object-contain" />
          ) : (
            <p className="text-sm text-slate-400">暂无分子图像</p>
          )}
        </div>

        <div className="rounded-md bg-slate-50 p-4 space-y-2 text-sm">
          <div className="flex justify-between"><span>分子式</span><b>{p?.formula ?? "-"}</b></div>
          <div className="flex justify-between"><span>分子量</span><b>{p?.molecular_weight ?? "-"}</b></div>
          <div className="flex justify-between"><span>LogP</span><b>{p?.logp ?? "-"}</b></div>
          <div className="flex justify-between"><span>HBD</span><b>{p?.hydrogen_bond_donors ?? "-"}</b></div>
          <div className="flex justify-between"><span>HBA</span><b>{p?.hydrogen_bond_acceptors ?? "-"}</b></div>
          <div className="flex justify-between"><span>LogP 来源</span><b>{p?.logp_source ?? "-"}</b></div>
        </div>
      </CardContent>
    </Card>
  );
}
