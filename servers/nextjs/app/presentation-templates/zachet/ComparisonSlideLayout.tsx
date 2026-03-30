import React from 'react'
import * as z from "zod";

export const layoutId = 'zachet-comparison-slide'
export const layoutName = 'Comparison'
export const layoutDescription = 'A two-column comparison slide for contrasting two concepts, approaches, or options. Best for pros/cons, before/after, or side-by-side analysis.'

const comparisonSlideSchema = z.object({
    title: z.string().min(3).max(60).default('Comparison').meta({
        description: "Slide title",
    }),
    description: z.string().min(10).max(150).default('A comparison of two key aspects or approaches related to the topic.').meta({
        description: "Brief description of what is being compared",
    }),
    left: z.object({
        heading: z.string().min(2).max(40).meta({ description: "Heading for the left column" }),
        points: z.array(z.string().min(5).max(100).meta({ description: "A comparison point" })).min(2).max(4).meta({ description: "List of points for the left column" }),
    }).default({
        heading: 'Option A',
        points: ['First advantage of this approach', 'Second advantage of this approach', 'Third advantage of this approach'],
    }).meta({ description: "Left column content" }),
    right: z.object({
        heading: z.string().min(2).max(40).meta({ description: "Heading for the right column" }),
        points: z.array(z.string().min(5).max(100).meta({ description: "A comparison point" })).min(2).max(4).meta({ description: "List of points for the right column" }),
    }).default({
        heading: 'Option B',
        points: ['First advantage of this approach', 'Second advantage of this approach', 'Third advantage of this approach'],
    }).meta({ description: "Right column content" }),
})

export const Schema = comparisonSlideSchema
export type ComparisonSlideData = z.infer<typeof comparisonSlideSchema>

interface ComparisonSlideLayoutProps { data?: Partial<ComparisonSlideData> }

const ComparisonSlideLayout: React.FC<ComparisonSlideLayoutProps> = ({ data: slideData }) => {
    const left = slideData?.left || { heading: 'Option A', points: [] }
    const right = slideData?.right || { heading: 'Option B', points: [] }

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
                    <div className="text-center mb-6">
                        <h1
                            className="font-bold mb-2"
                            style={{ fontSize: '42.7px', letterSpacing: '-1.6px', color: 'var(--background-text, #002BB2)' }}
                        >
                            {slideData?.title || 'Comparison'}
                        </h1>
                        <p style={{ fontSize: '16px', color: 'var(--background-text, #002BB2)', opacity: 0.7 }}>
                            {slideData?.description || ''}
                        </p>
                    </div>

                    <div className="flex gap-[36px] flex-1">
                        {/* Left card */}
                        <div className="flex-1 rounded p-[41px] flex flex-col" style={{ background: 'var(--card-color, #F7F8FF)', border: '1px solid var(--stroke, #F0F0F2)' }}>
                            <h2 className="font-bold mb-4" style={{ fontSize: '28.4px', color: 'var(--background-text, #002BB2)' }}>
                                {left.heading}
                            </h2>
                            <div className="flex flex-col gap-3">
                                {left.points?.map((point, i) => (
                                    <div key={i} className="flex items-start gap-3">
                                        <div className="w-2 h-2 rounded-[4px] mt-2 flex-shrink-0" style={{ background: 'var(--primary-color, #1F4CD9)' }} />
                                        <span style={{ fontSize: '15.3px', lineHeight: '1.5', color: 'var(--background-text, #002BB2)', opacity: 0.8 }}>{point}</span>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Right card */}
                        <div className="flex-1 rounded p-[41px] flex flex-col" style={{ background: 'var(--card-color, #F7F8FF)', border: '1px solid var(--stroke, #F0F0F2)' }}>
                            <h2 className="font-bold mb-4" style={{ fontSize: '28.4px', color: 'var(--background-text, #002BB2)' }}>
                                {right.heading}
                            </h2>
                            <div className="flex flex-col gap-3">
                                {right.points?.map((point, i) => (
                                    <div key={i} className="flex items-start gap-3">
                                        <div className="w-2 h-2 rounded-[4px] mt-2 flex-shrink-0" style={{ background: 'var(--stroke, #4C68DF)', opacity: 0.5 }} />
                                        <span style={{ fontSize: '15.3px', lineHeight: '1.5', color: 'var(--background-text, #002BB2)', opacity: 0.8 }}>{point}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </>
    )
}

export default ComparisonSlideLayout
