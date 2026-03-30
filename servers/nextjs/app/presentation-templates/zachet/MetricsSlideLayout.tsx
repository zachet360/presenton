import React from 'react'
import * as z from "zod";

export const layoutId = 'zachet-metrics-slide'
export const layoutName = 'Metrics'
export const layoutDescription = 'A slide for showcasing key numbers, statistics, or metrics in a grid layout. Best for highlighting quantitative data, KPIs, or achievements. No images.'

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

const MetricsSlideLayout: React.FC<MetricsSlideLayoutProps> = ({ data: slideData }) => {
    const metrics = slideData?.metrics || []

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

                <div className="flex-1 flex flex-col justify-center px-[72px] pt-[60px] pb-[40px]">
                    <h1
                        className="font-bold mb-2 text-center"
                        style={{ fontSize: '43px', letterSpacing: '-2px', color: 'var(--background-text, #002BB2)' }}
                    >
                        {slideData?.title || 'Key Metrics'}
                    </h1>
                    {slideData?.description && (
                        <p className="text-center mb-8 max-w-2xl mx-auto" style={{ fontSize: '15px', lineHeight: '1.6', color: 'var(--background-text, #002BB2)', opacity: 0.7 }}>
                            {slideData.description}
                        </p>
                    )}

                    <div className={`grid gap-[20px] max-w-4xl mx-auto w-full ${metrics.length <= 2 ? 'grid-cols-2' : metrics.length === 3 ? 'grid-cols-3' : 'grid-cols-4'}`}>
                        {metrics.map((metric, i) => (
                            <div
                                key={i}
                                className="text-center p-[28px] rounded"
                                style={{ background: 'var(--card-color, #F7F8FF)', border: '1px solid var(--stroke, #F0F0F2)' }}
                            >
                                <div
                                    className="font-bold mb-3"
                                    style={{ fontSize: '40px', color: 'var(--primary-color, #1F4CD9)' }}
                                >
                                    {metric.value}
                                </div>
                                <div
                                    className="font-semibold mb-1"
                                    style={{ fontSize: '15px', color: 'var(--background-text, #002BB2)' }}
                                >
                                    {metric.label}
                                </div>
                                <div
                                    style={{ fontSize: '13px', lineHeight: '1.5', color: 'var(--background-text, #002BB2)', opacity: 0.6 }}
                                >
                                    {metric.description}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </>
    )
}

export default MetricsSlideLayout
