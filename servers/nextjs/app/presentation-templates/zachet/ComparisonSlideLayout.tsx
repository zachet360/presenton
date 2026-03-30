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
        heading: z.string().min(2).max(40).meta({
            description: "Heading for the left column",
        }),
        points: z.array(
            z.string().min(5).max(100).meta({
                description: "A comparison point",
            })
        ).min(2).max(4).meta({
            description: "List of points for the left column",
        }),
    }).default({
        heading: 'Option A',
        points: ['First advantage of this approach', 'Second advantage of this approach', 'Third advantage of this approach'],
    }).meta({
        description: "Left column content",
    }),
    right: z.object({
        heading: z.string().min(2).max(40).meta({
            description: "Heading for the right column",
        }),
        points: z.array(
            z.string().min(5).max(100).meta({
                description: "A comparison point",
            })
        ).min(2).max(4).meta({
            description: "List of points for the right column",
        }),
    }).default({
        heading: 'Option B',
        points: ['First advantage of this approach', 'Second advantage of this approach', 'Third advantage of this approach'],
    }).meta({
        description: "Right column content",
    }),
})

export const Schema = comparisonSlideSchema

export type ComparisonSlideData = z.infer<typeof comparisonSlideSchema>

interface ComparisonSlideLayoutProps {
    data?: Partial<ComparisonSlideData>
}

const ComparisonSlideLayout: React.FC<ComparisonSlideLayoutProps> = ({ data: slideData }) => {
    const left = slideData?.left || { heading: 'Option A', points: [] }
    const right = slideData?.right || { heading: 'Option B', points: [] }

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
                    {slideData?.title || 'Comparison'}
                </h2>
                <p
                    className="text-base mb-6 text-center max-w-2xl mx-auto"
                    style={{ color: 'var(--background-text, #6b7280)' }}
                >
                    {slideData?.description || ''}
                </p>

                <div className="grid grid-cols-2 gap-6 flex-1">
                    {/* Left column */}
                    <div className="rounded-xl p-6" style={{ background: 'var(--card-color, #f9fafb)', border: '1px solid var(--stroke, #e5e7eb)' }}>
                        <h3
                            className="text-xl font-bold mb-4 pb-3"
                            style={{ color: 'var(--primary-color, #9333ea)', borderBottom: '2px solid var(--primary-color, #9333ea)' }}
                        >
                            {left.heading}
                        </h3>
                        <ul className="space-y-3">
                            {left.points?.map((point, i) => (
                                <li key={i} className="flex items-start gap-2">
                                    <span className="mt-1.5 w-2 h-2 rounded-full flex-shrink-0" style={{ background: 'var(--primary-color, #9333ea)' }} />
                                    <span className="text-sm leading-relaxed" style={{ color: 'var(--background-text, #374151)' }}>{point}</span>
                                </li>
                            ))}
                        </ul>
                    </div>

                    {/* Right column */}
                    <div className="rounded-xl p-6" style={{ background: 'var(--card-color, #f9fafb)', border: '1px solid var(--stroke, #e5e7eb)' }}>
                        <h3
                            className="text-xl font-bold mb-4 pb-3"
                            style={{ color: 'var(--background-text, #374151)', borderBottom: '2px solid var(--stroke, #d1d5db)' }}
                        >
                            {right.heading}
                        </h3>
                        <ul className="space-y-3">
                            {right.points?.map((point, i) => (
                                <li key={i} className="flex items-start gap-2">
                                    <span className="mt-1.5 w-2 h-2 rounded-full flex-shrink-0" style={{ background: 'var(--background-text, #9ca3af)' }} />
                                    <span className="text-sm leading-relaxed" style={{ color: 'var(--background-text, #374151)' }}>{point}</span>
                                </li>
                            ))}
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    )
}

export default ComparisonSlideLayout
