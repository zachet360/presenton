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

interface ClosingSlideLayoutProps { data?: Partial<ClosingSlideData> }

const ClosingSlideLayout: React.FC<ClosingSlideLayoutProps> = ({ data: slideData }) => {
    return (
        <>
            <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700&display=swap" rel="stylesheet" />
            <div
                className="w-full rounded-sm max-w-[1280px] shadow-lg max-h-[720px] aspect-video relative z-20 mx-auto overflow-hidden flex flex-col justify-center"
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

                <div className="px-[72px] max-w-3xl">
                    <h1
                        className="font-bold mb-4"
                        style={{ fontSize: '42px', letterSpacing: '-1px', color: 'var(--background-text, #002BB2)' }}
                    >
                        {slideData?.title || 'Thank You'}
                    </h1>
                    <p style={{ fontSize: '16px', lineHeight: '1.7', color: 'var(--background-text, #002BB2)', opacity: 0.7 }}>
                        {slideData?.summary || ''}
                    </p>
                </div>
            </div>
        </>
    )
}

export default ClosingSlideLayout
