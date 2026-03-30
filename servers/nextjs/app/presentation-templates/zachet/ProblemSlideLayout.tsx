import React from 'react'
import * as z from "zod";

export const layoutId = 'zachet-problem-slide'
export const layoutName = 'Research Problem'
export const layoutDescription = 'A slide defining the core research problem or challenge being addressed. Clearly states what issue the research aims to solve.'

const problemSlideSchema = z.object({
    title: z.string().min(3).max(30).default('Проблема').meta({
        description: "Slide title, typically 'Проблема' or 'Проблема исследования'",
    }),
    problem: z.string().min(30).max(400).default('The core research problem that this project aims to address.').meta({
        description: "Clear statement of the research problem in 2-4 sentences",
    }),
})

export const Schema = problemSlideSchema
export type ProblemSlideData = z.infer<typeof problemSlideSchema>

interface ProblemSlideLayoutProps { data?: Partial<ProblemSlideData> }

const ProblemSlideLayout: React.FC<ProblemSlideLayoutProps> = ({ data: slideData }) => {
    return (
        <>
            <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700&display=swap" rel="stylesheet" />
            <div
                className="w-full rounded-sm max-w-[1280px] shadow-lg max-h-[720px] aspect-video relative z-20 mx-auto overflow-hidden flex flex-col items-center justify-center"
                style={{ fontFamily: 'var(--body-font-family, Montserrat)', background: 'var(--background-color, #FFFFFF)' }}
            >
                {((slideData as any)?.__companyName__ || (slideData as any)?._logo_url__) && (
                    <div className="absolute top-5 left-5 flex items-center gap-2">
                        {(slideData as any)?._logo_url__ && <img src={(slideData as any)?._logo_url__} alt="logo" className="w-[60px] object-contain" />}
                        {(slideData as any)?.__companyName__ && (
                            <>
                                <div className="w-[2px] h-5" style={{ background: 'var(--stroke, #4C68DF)' }} />
                                <span className="text-sm font-semibold" style={{ color: 'var(--background-text, #002BB2)' }}>{(slideData as any)?.__companyName__}</span>
                            </>
                        )}
                    </div>
                )}

                <div className="text-center px-[100px] max-w-4xl">
                    <div
                        className="w-[56px] h-[56px] rounded-full flex items-center justify-center mx-auto mb-6"
                        style={{ background: '#E8453C' }}
                    >
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                            <circle cx="12" cy="12" r="10" />
                            <line x1="12" y1="8" x2="12" y2="12" />
                            <line x1="12" y1="16" x2="12.01" y2="16" />
                        </svg>
                    </div>
                    <h1
                        className="font-bold mb-4"
                        style={{ fontSize: '42.7px', letterSpacing: '-1.6px', color: 'var(--background-text, #002BB2)' }}
                    >
                        {slideData?.title || 'Проблема'}
                    </h1>
                    <div className="w-[60px] h-[4px] rounded-full mx-auto mb-6" style={{ background: '#E8453C' }} />
                    <p style={{ fontSize: '18px', lineHeight: '1.7', color: 'var(--background-text, #002BB2)', opacity: 0.8 }}>
                        {slideData?.problem || ''}
                    </p>
                </div>
            </div>
        </>
    )
}

export default ProblemSlideLayout
