import React from 'react'
import * as z from "zod";

export const layoutId = 'zachet-title-slide'
export const layoutName = 'Title Slide'
export const layoutDescription = 'Opening slide with presentation title, subtitle, and presenter info. Always used as the first slide.'

const titleSlideSchema = z.object({
    title: z.string().min(3).max(80).default('Presentation Title').meta({
        description: "Main title of the presentation",
    }),
    subtitle: z.string().min(5).max(120).default('A brief subtitle describing the topic of the presentation').meta({
        description: "Subtitle or tagline for the presentation",
    }),
    presenterName: z.string().min(2).max(50).default('Author Name').meta({
        description: "Name of the presenter or author",
    }),
    date: z.string().min(2).max(30).default('2026').meta({
        description: "Date of the presentation",
    }),
})

export const Schema = titleSlideSchema

export type TitleSlideData = z.infer<typeof titleSlideSchema>

interface TitleSlideLayoutProps {
    data?: Partial<TitleSlideData>
}

const TitleSlideLayout: React.FC<TitleSlideLayoutProps> = ({ data: slideData }) => {
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

            <div className="text-center px-16 max-w-4xl">
                <h1
                    className="text-5xl font-bold leading-tight mb-4"
                    style={{ color: 'var(--background-text, #111827)', lineHeight: '1.2' }}
                >
                    {slideData?.title || 'Presentation Title'}
                </h1>
                <div className="w-20 h-1 mx-auto mb-6" style={{ background: 'var(--primary-color, #9333ea)' }} />
                <p
                    className="text-xl mb-8 leading-relaxed"
                    style={{ color: 'var(--background-text, #6b7280)' }}
                >
                    {slideData?.subtitle || 'A brief subtitle describing the topic of the presentation'}
                </p>
                <div className="flex items-center justify-center gap-3">
                    <div
                        className="w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold"
                        style={{ background: 'var(--primary-color, #9333ea)', color: 'var(--primary-text, #ffffff)' }}
                    >
                        {(slideData?.presenterName || 'A').split(' ').map(w => w.charAt(0).toUpperCase()).join('')}
                    </div>
                    <div className="text-left">
                        <div className="text-base font-semibold" style={{ color: 'var(--background-text, #111827)' }}>
                            {slideData?.presenterName || 'Author Name'}
                        </div>
                        <div className="text-sm" style={{ color: 'var(--background-text, #9ca3af)' }}>
                            {slideData?.date || '2026'}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}

export default TitleSlideLayout
