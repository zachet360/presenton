import React from 'react'
import * as z from "zod";

export const layoutId = 'zachet-metrics-slide'
export const layoutName = 'Metrics'
export const layoutDescription = 'A slide for showcasing key numbers, statistics, or metrics. Best for highlighting quantitative data, KPIs, or achievements.'

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
    ]).meta({
        description: "List of metrics to display",
    }),
})

export const Schema = metricsSlideSchema

export type MetricsSlideData = z.infer<typeof metricsSlideSchema>

interface MetricsSlideLayoutProps {
    data?: Partial<MetricsSlideData>
}

const MetricsSlideLayout: React.FC<MetricsSlideLayoutProps> = ({ data: slideData }) => {
    const metrics = slideData?.metrics || []

    return (
        <div
            className="w-full rounded-sm max-w-[1280px] shadow-lg max-h-[720px] aspect-video relative z-20 mx-auto overflow-hidden flex flex-col"
            style={{
                fontFamily: 'var(--heading-font-family, Poppins)',
                background: 'var(--background-color, #ffffff)',
            }}
        >
            {((slideData as any)?.__companyName__ || (slideData as any)?._logo_url__) && (
                <div className="absolute top-0 left-0 right-0 px-12 pt-4">
                    <div className="flex items-center gap-1">
                        {(slideData as any)?._logo_url__ && <img src={(slideData as any)?._logo_url__} alt="logo" className="w-6 h-6" />}
                        {(slideData as any)?.__companyName__ && <span className="text-sm font-semibold" style={{ color: 'var(--background-text, #111827)' }}>{(slideData as any)?.__companyName__}</span>}
                    </div>
                </div>
            )}

            <div className="flex-1 flex flex-col justify-center px-12 pt-10 pb-10">
                <h2
                    className="text-4xl font-bold mb-2 text-center"
                    style={{ color: 'var(--background-text, #111827)' }}
                >
                    {slideData?.title || 'Key Metrics'}
                </h2>
                <p
                    className="text-base mb-8 text-center max-w-2xl mx-auto"
                    style={{ color: 'var(--background-text, #6b7280)' }}
                >
                    {slideData?.description || ''}
                </p>

                <div className={`grid gap-6 ${metrics.length <= 2 ? 'grid-cols-2' : metrics.length === 3 ? 'grid-cols-3' : 'grid-cols-4'} max-w-4xl mx-auto`}>
                    {metrics.map((metric, i) => (
                        <div
                            key={i}
                            className="text-center p-6 rounded-xl"
                            style={{ background: 'var(--card-color, #f9fafb)', border: '1px solid var(--stroke, #e5e7eb)' }}
                        >
                            <div
                                className="text-4xl font-bold mb-2"
                                style={{ color: 'var(--primary-color, #9333ea)' }}
                            >
                                {metric.value}
                            </div>
                            <div
                                className="text-sm font-semibold mb-1"
                                style={{ color: 'var(--background-text, #111827)' }}
                            >
                                {metric.label}
                            </div>
                            <div
                                className="text-xs leading-relaxed"
                                style={{ color: 'var(--background-text, #6b7280)' }}
                            >
                                {metric.description}
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    )
}

export default MetricsSlideLayout
