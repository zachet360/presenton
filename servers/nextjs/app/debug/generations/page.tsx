'use client'

import { useEffect, useState } from 'react'

interface LogSummary {
    id: string
    presentation_id: string | null
    filename: string
    status: string
    started_at: string | null
    finished_at: string | null
    total_duration_ms: number | null
    error: string | null
    steps_count: number
}

interface StepDetail {
    name: string
    started_at: string
    duration_ms: number | null
    input: any
    output: any
    error: string | null
    substeps?: any[]
}

interface LogDetail {
    id: string
    presentation_id: string | null
    filename: string
    status: string
    started_at: string | null
    finished_at: string | null
    total_duration_ms: number | null
    error: string | null
    steps: StepDetail[]
}

function formatDuration(ms: number | null): string {
    if (ms === null) return '—'
    if (ms < 1000) return `${ms}ms`
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`
    return `${Math.floor(ms / 60000)}m ${Math.round((ms % 60000) / 1000)}s`
}

function formatTime(iso: string | null): string {
    if (!iso) return '—'
    return new Date(iso).toLocaleString('ru-RU', {
        day: '2-digit', month: '2-digit', year: 'numeric',
        hour: '2-digit', minute: '2-digit', second: '2-digit',
    })
}

function StatusBadge({ status }: { status: string }) {
    const colors: Record<string, string> = {
        completed: 'bg-green-100 text-green-800',
        failed: 'bg-red-100 text-red-800',
        running: 'bg-yellow-100 text-yellow-800',
    }
    return (
        <span className={`px-2 py-0.5 rounded text-xs font-medium ${colors[status] || 'bg-gray-100 text-gray-800'}`}>
            {status}
        </span>
    )
}

function JsonBlock({ data, label }: { data: any; label: string }) {
    const [open, setOpen] = useState(false)
    if (data === null || data === undefined) return null
    return (
        <div className="mt-1">
            <button
                onClick={() => setOpen(!open)}
                className="text-xs text-blue-600 hover:text-blue-800 font-mono flex items-center gap-1"
            >
                <span>{open ? '▼' : '▶'}</span> {label}
            </button>
            {open && (
                <pre className="mt-1 p-3 bg-gray-50 border rounded text-xs overflow-auto max-h-96 whitespace-pre-wrap break-words">
                    {typeof data === 'string' ? data : JSON.stringify(data, null, 2)}
                </pre>
            )}
        </div>
    )
}

function StepCard({ step, index }: { step: StepDetail; index: number }) {
    const [open, setOpen] = useState(false)
    const hasError = !!step.error
    const borderColor = hasError ? 'border-red-300' : 'border-gray-200'

    return (
        <div className={`border ${borderColor} rounded-lg mb-2`}>
            <button
                onClick={() => setOpen(!open)}
                className="w-full px-4 py-3 flex items-center justify-between text-left hover:bg-gray-50"
            >
                <div className="flex items-center gap-3">
                    <span className="text-xs font-mono text-gray-400 w-6">{index + 1}</span>
                    <span className="font-medium text-sm">{step.name}</span>
                    {hasError && <span className="text-xs text-red-600 font-medium">ERROR</span>}
                </div>
                <div className="flex items-center gap-3">
                    <span className="text-xs text-gray-500 font-mono">
                        {formatDuration(step.duration_ms)}
                    </span>
                    <span className="text-gray-400">{open ? '▼' : '▶'}</span>
                </div>
            </button>
            {open && (
                <div className="px-4 pb-3 border-t border-gray-100">
                    <div className="text-xs text-gray-400 mt-2 mb-1">
                        Started: {formatTime(step.started_at)}
                    </div>
                    {step.error && (
                        <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-xs text-red-700">
                            {step.error}
                        </div>
                    )}
                    <JsonBlock data={step.input} label="Input" />
                    <JsonBlock data={step.output} label="Output" />
                    {step.substeps && step.substeps.length > 0 && (
                        <div className="mt-2">
                            <div className="text-xs font-medium text-gray-600 mb-1">
                                Substeps ({step.substeps.length})
                            </div>
                            {step.substeps.map((sub, i) => (
                                <JsonBlock key={i} data={sub} label={`Substep ${i + 1}`} />
                            ))}
                        </div>
                    )}
                </div>
            )}
        </div>
    )
}

export default function GenerationLogsPage() {
    const [logs, setLogs] = useState<LogSummary[]>([])
    const [search, setSearch] = useState('')
    const [selectedLog, setSelectedLog] = useState<LogDetail | null>(null)
    const [loading, setLoading] = useState(true)
    const [loadingDetail, setLoadingDetail] = useState(false)

    useEffect(() => {
        fetch('/api/v1/ppt/presentation/logs')
            .then(r => r.json())
            .then(data => { setLogs(data); setLoading(false) })
            .catch(() => setLoading(false))
    }, [])

    const filteredLogs = logs.filter(l =>
        l.filename.toLowerCase().includes(search.toLowerCase())
    )

    const openLog = async (id: string) => {
        if (selectedLog?.id === id) { setSelectedLog(null); return }
        setLoadingDetail(true)
        try {
            const r = await fetch(`/api/v1/ppt/presentation/logs/${id}`)
            const data = await r.json()
            setSelectedLog(data)
        } catch { }
        setLoadingDetail(false)
    }

    return (
        <div className="min-h-screen bg-white p-6 max-w-5xl mx-auto" style={{ fontFamily: 'system-ui, sans-serif' }}>
            <h1 className="text-2xl font-bold mb-1">Generation Logs</h1>
            <p className="text-sm text-gray-500 mb-6">Step-by-step trace of each presentation generation</p>

            <input
                type="text"
                placeholder="Search by filename..."
                value={search}
                onChange={e => setSearch(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg mb-4 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />

            {loading ? (
                <div className="text-center text-gray-400 py-12">Loading...</div>
            ) : filteredLogs.length === 0 ? (
                <div className="text-center text-gray-400 py-12">No logs found</div>
            ) : (
                <div className="space-y-2">
                    {filteredLogs.map(lg => (
                        <div key={lg.id}>
                            <button
                                onClick={() => openLog(lg.id)}
                                className={`w-full text-left px-4 py-3 border rounded-lg hover:bg-gray-50 transition ${selectedLog?.id === lg.id ? 'border-blue-400 bg-blue-50' : 'border-gray-200'}`}
                            >
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-3">
                                        <span className="font-medium text-sm">{lg.filename}</span>
                                        <StatusBadge status={lg.status} />
                                    </div>
                                    <div className="flex items-center gap-4 text-xs text-gray-500">
                                        <span>{lg.steps_count} steps</span>
                                        <span className="font-mono">{formatDuration(lg.total_duration_ms)}</span>
                                        <span>{formatTime(lg.started_at)}</span>
                                    </div>
                                </div>
                                {lg.error && (
                                    <div className="text-xs text-red-600 mt-1 truncate">{lg.error}</div>
                                )}
                            </button>

                            {selectedLog?.id === lg.id && (
                                <div className="mt-2 ml-4 mb-4">
                                    {loadingDetail ? (
                                        <div className="text-sm text-gray-400 py-4">Loading steps...</div>
                                    ) : (
                                        <>
                                            <div className="flex items-center gap-6 text-xs text-gray-500 mb-3 pb-2 border-b">
                                                <span>Presentation: <span className="font-mono">{selectedLog.presentation_id || '—'}</span></span>
                                                <span>Total: <span className="font-mono font-bold">{formatDuration(selectedLog.total_duration_ms)}</span></span>
                                                <span>Started: {formatTime(selectedLog.started_at)}</span>
                                                <span>Finished: {formatTime(selectedLog.finished_at)}</span>
                                            </div>
                                            {selectedLog.steps.map((step, i) => (
                                                <StepCard key={i} step={step} index={i} />
                                            ))}
                                        </>
                                    )}
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            )}
        </div>
    )
}
