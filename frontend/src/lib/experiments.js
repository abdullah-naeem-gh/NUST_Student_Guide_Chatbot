const METHOD_META = [
  { key: 'hybrid', label: 'Hybrid', color: '#146b5d' },
  { key: 'tfidf', label: 'TFIDF', color: '#2563eb' },
  { key: 'simhash', label: 'Simhash', color: '#9333ea' },
  { key: 'minhash', label: 'Minhash', color: '#ea580c' },
]

function safeNumber(value) {
  return Number.isFinite(value) ? value : 0
}

function precisionAtK(row, k) {
  const relevant = new Set(Array.isArray(row?.relevant_chunk_ids) ? row.relevant_chunk_ids : [])
  const retrieved = Array.isArray(row?.retrieved_chunk_ids) ? row.retrieved_chunk_ids.slice(0, k) : []
  if (k <= 0) return 0
  let hit = 0
  for (const id of retrieved) {
    if (relevant.has(id)) hit += 1
  }
  return hit / k
}

function meanPrecisionAtK(rows, k) {
  if (!Array.isArray(rows) || rows.length === 0) return 0
  const total = rows.reduce((acc, row) => acc + precisionAtK(row, k), 0)
  return total / rows.length
}

export function buildPrecisionSeries(experiments) {
  const perQuery = experiments?.method_comparison?.per_query ?? {}
  const ks = [1, 3, 5, 10]

  return ks.map((k) => {
    const point = { k: String(k) }
    for (const method of METHOD_META) {
      point[method.label] = safeNumber(meanPrecisionAtK(perQuery[method.key], k))
    }
    return point
  })
}

export function buildLatencySeries(experiments) {
  const summary = experiments?.method_comparison?.summary ?? {}
  return METHOD_META.map((method) => ({
    method: method.label,
    latencyMs: safeNumber(summary?.[method.key]?.['mean_latency_ms']),
    color: method.color,
  }))
}

export function buildScalabilitySeries(experiments) {
  const summary = experiments?.method_comparison?.summary ?? {}
  const points = Array.isArray(experiments?.scalability?.points) ? [...experiments.scalability.points] : []
  points.sort((a, b) => safeNumber(a.scale) - safeNumber(b.scale))

  const baseline = {
    scale: '1x',
    TFIDF: safeNumber(summary?.tfidf?.['mean_latency_ms']),
    Minhash: safeNumber(summary?.minhash?.['mean_latency_ms']),
    Simhash: safeNumber(summary?.simhash?.['mean_latency_ms']),
  }

  const scaled = points.map((point) => ({
    scale: `${safeNumber(point.scale)}x`,
    TFIDF: safeNumber(point?.mean_query_latency_ms?.tfidf),
    Minhash: safeNumber(point?.mean_query_latency_ms?.minhash),
    Simhash: safeNumber(point?.mean_query_latency_ms?.simhash),
  }))

  return [baseline, ...scaled]
}

export function buildSensitivitySeries(experiments) {
  const sensitivity = experiments?.parameter_sensitivity ?? {}

  const minhash = (Array.isArray(sensitivity.minhash) ? sensitivity.minhash : []).map((row) => ({
    x: String(row.num_perm),
    value: safeNumber(row['mean_recall@5']),
  }))
  const lsh = (Array.isArray(sensitivity.lsh) ? sensitivity.lsh : []).map((row) => ({
    x: String(row.num_bands),
    value: safeNumber(row['mean_recall@5']),
  }))
  const simhash = (Array.isArray(sensitivity.simhash) ? sensitivity.simhash : []).map((row) => ({
    x: String(row.hamming_threshold),
    value: safeNumber(row['mean_precision@5']),
  }))

  return { minhash, lsh, simhash }
}

export function buildMetricsSummary(experiments) {
  const summary = experiments?.method_comparison?.summary ?? {}
  const perQuery = experiments?.method_comparison?.per_query ?? {}

  return METHOD_META.map((method) => {
    const methodSummary = summary?.[method.key] ?? {}
    return {
      method: method.label,
      p1: safeNumber(methodSummary['mean_p@1']),
      p3: safeNumber(methodSummary['mean_p@3']),
      p5: safeNumber(methodSummary['mean_p@5']),
      p10: safeNumber(meanPrecisionAtK(perQuery[method.key], 10)),
      r5: safeNumber(methodSummary['mean_r@5']),
      map5: safeNumber(methodSummary['map@5']),
      latencyMs: safeNumber(methodSummary['mean_latency_ms']),
      memoryMb: safeNumber(methodSummary['mean_memory_mb']),
    }
  })
}

export const EXPERIMENT_METHODS = METHOD_META
