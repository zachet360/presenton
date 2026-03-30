import React from 'react'
import * as z from "zod";

export const layoutId = 'zachet-metrics-slide'
export const layoutName = 'Metrics'
export const layoutDescription = 'A slide for showcasing key numbers, statistics, or metrics with visual bar indicators. Best for highlighting quantitative data, KPIs, or achievements. No image needed — metrics are visualized as infographic bars.'

const metricsSlideSchema = z.object({
    title: z.string().min(3).max(60).default('Key Metrics').meta({
        description: "Slide title",
    }),
    description: z.string().min(10).max(150).default('An overview of the most important metrics and numbers related to this topic.').meta({
        description: "Brief description of the metrics context",
    }),
    metrics: z.array(z.object({
        value: z.string().min(1).max(12).meta({
            description: "Metric value (e.g., 95%, 150+, $2M). Keep short.",
        }),
        label: z.string().min(2).max(40).meta({
            description: "Metric label/name",
        }),
        description: z.string().min(5).max(100).meta({
            description: "Brief explanation of the metric",
        }),
    })).min(2).max(4).default([
        { value: '95%', label: 'Success Rate', description: 'Percentage of successfully completed tasks' },
        { value: '150+', label: 'Projects', description: 'Total number of completed projects' },
        { value: '24/7', label: 'Availability', description: 'Round-the-clock service availability' },
    ]).meta({ description: "List of metrics to display" }),
})

export const Schema = metricsSlideSchema
export type MetricsSlideData = z.infer<typeof metricsSlideSchema>

interface MetricsSlideLayoutProps { data?: Partial<MetricsSlideData> }

function parseNumericValue(value: string): number | null {
    const cleaned = value.replace(/[^0-9.,]/g, '').replace(',', '.')
    const num = parseFloat(cleaned)
    return isNaN(num) ? null : num
}

const BAR_COLORS = ['#1F4CD9', '#6B89E6', '#4C68DF', '#3E61DE']

const MetricsSlideLayout: React.FC<MetricsSlideLayoutProps> = ({ data: slideData }) => {
    const metrics = slideData?.metrics || []

    const numericValues = metrics.map(m => parseNumericValue(m.value))
    const maxVal = Math.max(...numericValues.filter((v): v is number => v !== null), 1)

    return (
        <>
            <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700&display=swap" rel="stylesheet" />
            <div
                className="w-full rounded-sm max-w-[1280px] shadow-lg max-h-[720px] aspect-video relative z-20 mx-auto overflow-hidden flex flex-col"
                style={{ fontFamily: 'var(--body-font-family, Montserrat)', background: 'var(--background-color, #FFFFFF)' }}
            >
                {((slideData as any)?.__companyName__ || (slideData as any)?._logo_url__) && (
                    <div className="absolute top-5 left-5 flex items-center gap-2 z-10">
                        {(slideData as any)?._logo_url__ && <img src={(slideData as any)?._logo_url__} alt="logo" className="w-[60px] object-contain" />}
                        {(slideData as any)?.__companyName__ && (
                            <>
                                <div className="w-[2px] h-5" style={{ background: 'var(--stroke, #4C68DF)' }} />
                                <span className="text-sm font-semibold" style={{ color: 'var(--background-text, #002BB2)' }}>{(slideData as any)?.__companyName__}</span>
                            </>
                        )}
                    </div>
                )}

                <div className="flex-1 flex px-[72px] pt-[60px] pb-[40px] gap-[60px]">
                    {/* Left: Title + description */}
                    <div className="w-[40%] flex flex-col justify-center">
                        <h1
                            className="font-bold mb-4"
                            style={{ fontSize: '42.7px', letterSpacing: '-1.6px', lineHeight: '1.1', color: 'var(--background-text, #002BB2)' }}
                        >
                            {slideData?.title || 'Key Metrics'}
                        </h1>
                        <div className="w-[60px] h-[4px] rounded-[4px] mb-5" style={{ background: 'var(--primary-color, #1F4CD9)' }} />
                        <p style={{ fontSize: '16px', lineHeight: '1.7', color: 'var(--background-text, #002BB2)', opacity: 0.7 }}>
                            {slideData?.description || ''}
                        </p>
                    </div>

                    {/* Right: Metric cards with bars */}
                    <div className="w-[60%] flex flex-col justify-center gap-[20px]">
                        {metrics.map((metric, i) => {
                            const numVal = numericValues[i]
                            const barWidth = numVal !== null ? Math.max((numVal / maxVal) * 100, 8) : 50
                            const color = BAR_COLORS[i % BAR_COLORS.length]

                            return (
                                <div
                                    key={i}
                                    className="rounded p-[28px]"
                                    style={{ background: 'var(--card-color, #F7F8FF)', border: '1px solid var(--stroke, #F0F0F2)' }}
                                >
                                    <div className="flex items-baseline justify-between mb-2">
                                        <div>
                                            <span className="font-bold" style={{ fontSize: '15px', color: 'var(--background-text, #002BB2)' }}>
                                                {metric.label}
                                            </span>
                                            <span style={{ fontSize: '13px', color: 'var(--background-text, #002BB2)', opacity: 0.5, marginLeft: '12px' }}>
                                                {metric.description}
                                            </span>
                                        </div>
                                        <span className="font-bold flex-shrink-0 ml-4" style={{ fontSize: '32px', color }}>
                                            {metric.value}
                                        </span>
                                    </div>
                                    <div className="w-full h-[8px] rounded-[4px] overflow-hidden" style={{ background: 'var(--stroke, #F0F0F2)' }}>
                                        <div
                                            className="h-full rounded-[4px] transition-all"
                                            style={{ width: `${barWidth}%`, background: color }}
                                        />
                                    </div>
                                </div>
                            )
                        })}
                    </div>
                </div>
            </div>
        </>
    )
}

export default MetricsSlideLayout
