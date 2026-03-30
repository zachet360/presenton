import React from 'react'
import * as z from "zod";

export const layoutId = 'zachet-perspectives-slide'
export const layoutName = 'Research Perspectives'
export const layoutDescription = 'A slide presenting future research perspectives, recommendations, or directions for further study. Placed before the closing slide in academic presentations.'

const perspectivesSlideSchema = z.object({
    title: z.string().min(3).max(50).default('Перспективы исследований').meta({
        description: "Slide title, e.g. 'Перспективы исследований', 'Рекомендации', 'Направления дальнейшей работы'",
    }),
    description: z.string().min(10).max(180).default('Key directions for future research and practical recommendations.').meta({
        description: "Brief introductory text about the future directions",
    }),
    points: z.array(
        z.string().min(10).max(150).meta({
            description: "A specific recommendation or future research direction",
        })
    ).min(2).max(5).default([
        'First research direction or recommendation',
        'Second research direction or recommendation',
        'Third research direction or recommendation',
    ]).meta({
        description: "List of future perspectives or recommendations",
    }),
})

export const Schema = perspectivesSlideSchema
export type PerspectivesSlideData = z.infer<typeof perspectivesSlideSchema>

interface PerspectivesSlideLayoutProps { data?: Partial<PerspectivesSlideData> }

const PerspectivesSlideLayout: React.FC<PerspectivesSlideLayoutProps> = ({ data: slideData }) => {
    const points = slideData?.points || []

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
                        className="font-bold mb-2"
                        style={{ fontSize: '42.7px', letterSpacing: '-1.6px', lineHeight: '1.1', color: 'var(--background-text, #002BB2)' }}
                    >
                        {slideData?.title || 'Перспективы исследований'}
                    </h1>
                    <p className="mb-6 max-w-2xl" style={{ fontSize: '16px', lineHeight: '1.6', color: 'var(--background-text, #002BB2)', opacity: 0.7 }}>
                        {slideData?.description || ''}
                    </p>

                    <div className="flex flex-col gap-[14px]">
                        {points.map((point, i) => (
                            <div
                                key={i}
                                className="flex items-start gap-4 p-5 rounded"
                                style={{ background: i === 0 ? 'var(--primary-color, #6B89E6)' : 'var(--card-color, #F7F8FF)', border: i === 0 ? 'none' : '1px solid var(--stroke, #F0F0F2)' }}
                            >
                                <div
                                    className="w-[32px] h-[32px] rounded-full flex items-center justify-center flex-shrink-0"
                                    style={{ background: i === 0 ? 'rgba(255,255,255,0.2)' : 'var(--primary-color, #1F4CD9)' }}
                                >
                                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={i === 0 ? '#FFFFFF' : 'var(--primary-text, #FFFFFF)'} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                                        <polyline points="13 17 18 12 13 7" />
                                        <polyline points="6 17 11 12 6 7" />
                                    </svg>
                                </div>
                                <p className="pt-1" style={{ fontSize: '15.3px', lineHeight: '1.5', color: i === 0 ? '#FFFFFF' : 'var(--background-text, #002BB2)', opacity: i === 0 ? 1 : 0.8 }}>
                                    {point}
                                </p>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </>
    )
}

export default PerspectivesSlideLayout
