import React from 'react'
import * as z from "zod";
import { ImageSchema } from '../defaultSchemes';

export const layoutId = 'zachet-metrics-slide'
export const layoutName = 'Metrics with Infographic'
export const layoutDescription = 'A slide for showcasing key numbers and statistics on the left with a YandexART-generated infographic on the right. Best for highlighting quantitative data, KPIs, or achievements.'

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
    ]).meta({ description: "List of metrics to display" }),
    image: ImageSchema.default({
        __image_url__: '',
        __image_prompt__: 'statistics infographic chart',
    }).meta({
        description: "AI-generated infographic visualizing the metrics data",
    }),
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
                className="w-full rounded-sm max-w-[1280px] shadow-lg max-h-[720px] aspect-video relative z-20 mx-auto overflow-hidden flex"
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

                {/* Left: Title + Metrics */}
                <div className="w-[50%] flex flex-col justify-center px-[52px] pt-[60px] pb-[40px]">
                    <h1
                        className="font-bold mb-6"
                        style={{ fontSize: '42px', letterSpacing: '-1px', lineHeight: '1.1', color: 'var(--background-text, #002BB2)' }}
                    >
                        {slideData?.title || 'Key Metrics'}
                    </h1>
                    <div className="flex flex-col gap-[16px]">
                        {metrics.map((metric, i) => (
                            <div
                                key={i}
                                className="flex items-center gap-4 p-4 rounded"
                                style={{ background: 'var(--card-color, #F7F8FF)', border: '1px solid var(--stroke, #F0F0F2)' }}
                            >
                                <div
                                    className="text-3xl font-bold flex-shrink-0 min-w-[70px] text-center"
                                    style={{ color: 'var(--primary-color, #1F4CD9)' }}
                                >
                                    {metric.value}
                                </div>
                                <div>
                                    <div className="text-sm font-semibold" style={{ color: 'var(--background-text, #002BB2)' }}>
                                        {metric.label}
                                    </div>
                                    <div className="text-xs mt-0.5" style={{ color: 'var(--background-text, #002BB2)', opacity: 0.6 }}>
                                        {metric.description}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Right: Infographic from YandexART */}
                <div className="w-[50%] p-[20px] flex items-center justify-center">
                    {slideData?.image?.__image_url__ ? (
                        <img
                            src={slideData.image.__image_url__}
                            alt={slideData.image.__image_prompt__ || slideData?.title || ''}
                            className="max-w-full max-h-full rounded-lg object-contain"
                        />
                    ) : (
                        <div className="w-full aspect-video rounded-lg flex items-center justify-center" style={{ background: 'var(--card-color, #F7F8FF)' }}>
                            <span style={{ fontSize: '14px', color: 'var(--background-text, #002BB2)', opacity: 0.3 }}>Infographic</span>
                        </div>
                    )}
                </div>
            </div>
        </>
    )
}

export default MetricsSlideLayout
