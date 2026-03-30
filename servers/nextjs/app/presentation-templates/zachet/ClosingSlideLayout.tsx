import React from 'react'
import * as z from "zod";

export const layoutId = 'zachet-closing-slide'
export const layoutName = 'Closing Slide'
export const layoutDescription = 'Final slide with a closing message and summary. Always used as the last slide of the presentation.'

const closingSlideSchema = z.object({
    title: z.string().min(3).max(60).default('Thank You').meta({
        description: "Closing title or message",
    }),
    summary: z.string().min(10).max(200).default('This presentation covered the key aspects of the topic. Thank you for your attention.').meta({
        description: "Brief closing summary or final thoughts",
    }),
})

export const Schema = closingSlideSchema

export type ClosingSlideData = z.infer<typeof closingSlideSchema>

interface ClosingSlideLayoutProps {
    data?: Partial<ClosingSlideData>
}

const ClosingSlideLayout: React.FC<ClosingSlideLayoutProps> = ({ data: slideData }) => {
    return (
        <div
            className="w-full rounded-sm max-w-[1280px] shadow-lg max-h-[720px] aspect-video relative z-20 mx-auto overflow-hidden flex flex-col items-center justify-center"
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

            <div className="text-center px-16 max-w-3xl">
                <div
                    className="w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-6"
                    style={{ background: 'var(--primary-color, #9333ea)' }}
                >
                    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--primary-text, #ffffff)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M20 6L9 17l-5-5" />
                    </svg>
                </div>
                <h2
                    className="text-5xl font-bold mb-4"
                    style={{ color: 'var(--background-text, #111827)' }}
                >
                    {slideData?.title || 'Thank You'}
                </h2>
                <div className="w-20 h-1 mx-auto mb-6" style={{ background: 'var(--primary-color, #9333ea)' }} />
                <p
                    className="text-lg leading-relaxed"
                    style={{ color: 'var(--background-text, #6b7280)' }}
                >
                    {slideData?.summary || 'This presentation covered the key aspects of the topic. Thank you for your attention.'}
                </p>
            </div>
        </div>
    )
}

export default ClosingSlideLayout
