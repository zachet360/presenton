import React from 'react'
import * as z from "zod";

export const layoutId = 'zachet-goal-slide'
export const layoutName = 'Research Goal'
export const layoutDescription = 'A slide stating the main goal/objective of the research project. Must clearly define the primary research aim in 1-2 sentences.'

const goalSlideSchema = z.object({
    title: z.string().min(3).max(30).default('Цель').meta({
        description: "Slide title, typically 'Цель' or 'Цель исследования'",
    }),
    goal: z.string().min(20).max(300).default('The main goal of this research project.').meta({
        description: "The primary research goal stated clearly in 1-2 sentences",
    }),
})

export const Schema = goalSlideSchema
export type GoalSlideData = z.infer<typeof goalSlideSchema>

interface GoalSlideLayoutProps { data?: Partial<GoalSlideData> }

const GoalSlideLayout: React.FC<GoalSlideLayoutProps> = ({ data: slideData }) => {
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
                        className="w-[56px] h-[56px] rounded-[4px] flex items-center justify-center mx-auto mb-6"
                        style={{ background: 'var(--primary-color, #1F4CD9)' }}
                    >
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--primary-text, #FFFFFF)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                            <circle cx="12" cy="12" r="10" />
                            <circle cx="12" cy="12" r="6" />
                            <circle cx="12" cy="12" r="2" />
                        </svg>
                    </div>
                    <h1
                        className="font-bold mb-4"
                        style={{ fontSize: '42.7px', letterSpacing: '-1.6px', color: 'var(--background-text, #002BB2)' }}
                    >
                        {slideData?.title || 'Цель'}
                    </h1>
                    <div className="w-[60px] h-[4px] rounded-[4px] mx-auto mb-6" style={{ background: 'var(--primary-color, #1F4CD9)' }} />
                    <p style={{ fontSize: '20px', lineHeight: '1.7', color: 'var(--background-text, #002BB2)', opacity: 0.8 }}>
                        {slideData?.goal || ''}
                    </p>
                </div>
            </div>
        </>
    )
}

export default GoalSlideLayout
