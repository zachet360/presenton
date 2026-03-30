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

interface TitleSlideLayoutProps { data?: Partial<TitleSlideData> }

const TitleSlideLayout: React.FC<TitleSlideLayoutProps> = ({ data: slideData }) => {
    return (
        <>
            <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700&display=swap" rel="stylesheet" />
            <div
                className="w-full rounded-sm max-w-[1280px] shadow-lg max-h-[720px] aspect-video relative z-20 mx-auto overflow-hidden flex flex-col"
                style={{ fontFamily: 'var(--body-font-family, Montserrat)', background: 'var(--background-color, #FFFFFF)' }}
            >
                {/* Top: Cover image */}
                <div className="h-[55%] w-full relative overflow-hidden">
                    {slideData?.image?.__image_url__ ? (
                        <img
                            src={slideData.image.__image_url__}
                            alt={slideData.image.__image_prompt__ || slideData?.title || ''}
                            className="w-full h-full object-cover"
                        />
                    ) : (
                        <div className="w-full h-full" style={{ background: 'var(--card-color, #F7F8FF)' }} />
                    )}
                    {((slideData as any)?.__companyName__ || (slideData as any)?._logo_url__) && (
                        <div className="absolute top-5 left-5 flex items-center gap-2">
                            {(slideData as any)?._logo_url__ && <img src={(slideData as any)?._logo_url__} alt="logo" className="w-[60px] object-contain" />}
                            {(slideData as any)?.__companyName__ && (
                                <>
                                    <div className="w-[2px] h-5" style={{ background: 'rgba(255,255,255,0.6)' }} />
                                    <span className="text-sm font-semibold text-white drop-shadow">{(slideData as any)?.__companyName__}</span>
                                </>
                            )}
                        </div>
                    )}
                </div>

                {/* Bottom: Title + info */}
                <div className="h-[45%] flex flex-col items-center justify-center px-[72px]">
                    <h1
                        className="font-bold text-center leading-tight mb-2"
                        style={{ fontSize: '42.7px', letterSpacing: '-1.6px', color: 'var(--background-text, #002BB2)' }}
                    >
                        {slideData?.title || 'Presentation Title'}
                    </h1>
                    <div className="w-[60px] h-[4px] rounded-full mb-3" style={{ background: 'var(--primary-color, #1F4CD9)' }} />
                    <p
                        className="text-center max-w-2xl mb-4"
                        style={{ fontSize: '16px', lineHeight: '1.6', color: 'var(--background-text, #002BB2)', opacity: 0.7 }}
                    >
                        {slideData?.subtitle || ''}
                    </p>
                    <div className="flex items-center gap-3">
                        <div
                            className="w-9 h-9 rounded-full flex items-center justify-center text-xs font-bold"
                            style={{ background: 'var(--primary-color, #1F4CD9)', color: 'var(--primary-text, #FFFFFF)' }}
                        >
                            {(slideData?.presenterName || 'A').split(' ').map(w => w.charAt(0).toUpperCase()).join('')}
                        </div>
                        <div>
                            <div className="text-sm font-semibold" style={{ color: 'var(--background-text, #002BB2)' }}>
                                {slideData?.presenterName || 'Author Name'}
                            </div>
                            <div style={{ fontSize: '12px', color: 'var(--background-text, #002BB2)', opacity: 0.5 }}>
                                {slideData?.date || '2026'}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </>
    )
}

export default TitleSlideLayout
