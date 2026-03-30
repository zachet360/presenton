import React from 'react'
import * as z from "zod";
import { ImageSchema } from '../defaultSchemes';

export const layoutId = 'zachet-title-slide'
export const layoutName = 'Title Slide'
export const layoutDescription = 'Opening slide with a cover image on top and presentation title, subtitle, and presenter info on the bottom. Always used as the first slide.'

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
    image: ImageSchema.default({
        __image_url__: '',
        __image_prompt__: 'presentation cover image',
    }).meta({
        description: "Cover image for the title slide",
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
            className="w-full rounded-sm max-w-[1280px] shadow-lg max-h-[720px] aspect-video relative z-20 mx-auto overflow-hidden flex flex-col"
            style={{
                fontFamily: 'var(--heading-font-family, Poppins)',
                background: 'var(--background-color, #ffffff)',
            }}
        >
            {/* Top: Cover image */}
            <div className="h-1/2 w-full relative overflow-hidden">
                {slideData?.image?.__image_url__ ? (
                    <img
                        src={slideData.image.__image_url__}
                        alt={slideData.image.__image_prompt__ || slideData?.title || ''}
                        className="w-full h-full object-cover"
                    />
                ) : (
                    <div className="w-full h-full" style={{ background: 'var(--card-color, #f3f4f6)' }} />
                )}
                {((slideData as any)?.__companyName__ || (slideData as any)?._logo_url__) && (
                    <div className="absolute top-0 left-0 px-8 pt-4">
                        <div className="flex items-center gap-1">
                            {(slideData as any)?._logo_url__ && <img src={(slideData as any)?._logo_url__} alt="logo" className="w-6 h-6" />}
                            {(slideData as any)?.__companyName__ && <span className="text-sm font-semibold text-white drop-shadow">{(slideData as any)?.__companyName__}</span>}
                        </div>
                    </div>
                )}
            </div>

            {/* Bottom: Title + info */}
            <div className="h-1/2 flex flex-col items-center justify-center px-12">
                <h1
                    className="text-4xl font-bold leading-tight mb-2 text-center"
                    style={{ color: 'var(--background-text, #111827)' }}
                >
                    {slideData?.title || 'Presentation Title'}
                </h1>
                <div className="w-16 h-1 mb-3" style={{ background: 'var(--primary-color, #9333ea)' }} />
                <p
                    className="text-base mb-4 text-center max-w-2xl"
                    style={{ color: 'var(--background-text, #6b7280)' }}
                >
                    {slideData?.subtitle || 'A brief subtitle describing the topic of the presentation'}
                </p>
                <div className="flex items-center gap-2">
                    <div
                        className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold"
                        style={{ background: 'var(--primary-color, #9333ea)', color: 'var(--primary-text, #ffffff)' }}
                    >
                        {(slideData?.presenterName || 'A').split(' ').map(w => w.charAt(0).toUpperCase()).join('')}
                    </div>
                    <div className="text-left">
                        <div className="text-sm font-semibold" style={{ color: 'var(--background-text, #111827)' }}>
                            {slideData?.presenterName || 'Author Name'}
                        </div>
                        <div className="text-xs" style={{ color: 'var(--background-text, #9ca3af)' }}>
                            {slideData?.date || '2026'}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}

export default TitleSlideLayout
