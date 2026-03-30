import React from 'react'
import * as z from "zod";
import { ImageSchema } from '../defaultSchemes';

export const layoutId = 'zachet-metrics-slide'
export const layoutName = 'Metrics with Infographic'
export const layoutDescription = 'A slide for showcasing key numbers and statistics on the left with a supporting infographic or chart image on the right. Best for highlighting quantitative data, KPIs, or achievements.'

const metricsSlideSchema = z.object({
    title: z.string().min(3).max(60).default('Key Metrics').meta({
        description: "Slide title",
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
    image: ImageSchema.default({
        __image_url__: '',
        __image_prompt__: 'statistics infographic chart',
    }).meta({
        description: "Infographic, chart, or diagram illustrating the metrics",
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
            className="w-full rounded-sm max-w-[1280px] shadow-lg max-h-[720px] aspect-video relative z-20 mx-auto overflow-hidden flex"
            style={{
                fontFamily: 'var(--heading-font-family, Poppins)',
                background: 'var(--background-color, #ffffff)',
            }}
        >
            {((slideData as any)?.__companyName__ || (slideData as any)?._logo_url__) && (
                <div className="absolute top-0 left-0 right-0 px-12 pt-4 z-10">
                    <div className="flex items-center gap-1">
                        {(slideData as any)?._logo_url__ && <img src={(slideData as any)?._logo_url__} alt="logo" className="w-6 h-6" />}
                        {(slideData as any)?.__companyName__ && <span className="text-sm font-semibold" style={{ color: 'var(--background-text, #111827)' }}>{(slideData as any)?.__companyName__}</span>}
                    </div>
                </div>
            )}

            {/* Left: Title + Metrics */}
            <div className="w-1/2 flex flex-col justify-center px-12 pt-10 pb-10">
                <h2
                    className="text-3xl font-bold mb-6"
                    style={{ color: 'var(--background-text, #111827)' }}
                >
                    {slideData?.title || 'Key Metrics'}
                </h2>

                <div className="grid grid-cols-1 gap-4">
                    {metrics.map((metric, i) => (
                        <div
                            key={i}
                            className="flex items-center gap-4 p-4 rounded-xl"
                            style={{ background: 'var(--card-color, #f9fafb)', border: '1px solid var(--stroke, #e5e7eb)' }}
                        >
                            <div
                                className="text-3xl font-bold flex-shrink-0 min-w-[70px] text-center"
                                style={{ color: 'var(--primary-color, #9333ea)' }}
                            >
                                {metric.value}
                            </div>
                            <div>
                                <div
                                    className="text-sm font-semibold"
                                    style={{ color: 'var(--background-text, #111827)' }}
                                >
                                    {metric.label}
                                </div>
                                <div
                                    className="text-xs leading-relaxed mt-0.5"
                                    style={{ color: 'var(--background-text, #6b7280)' }}
                                >
                                    {metric.description}
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Right: Infographic */}
            <div className="w-1/2 p-6 flex items-center justify-center">
                {slideData?.image?.__image_url__ ? (
                    <img
                        src={slideData.image.__image_url__}
                        alt={slideData.image.__image_prompt__ || slideData?.title || ''}
                        className="max-w-full max-h-full rounded-xl object-contain"
                    />
                ) : (
                    <div className="w-full aspect-video rounded-xl flex items-center justify-center" style={{ background: 'var(--card-color, #f3f4f6)' }}>
                        <span className="text-sm" style={{ color: 'var(--background-text, #9ca3af)' }}>Infographic</span>
                    </div>
                )}
            </div>
        </div>
    )
}

export default MetricsSlideLayout
