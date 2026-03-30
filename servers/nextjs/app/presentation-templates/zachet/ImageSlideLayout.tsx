import React from 'react'
import * as z from "zod";
import { ImageSchema } from '../defaultSchemes';

export const layoutId = 'zachet-image-slide'
export const layoutName = 'Image with Text'
export const layoutDescription = 'A slide with a title, description text on the left, and a supporting image on the right. Best for illustrating concepts with visuals.'

const imageSlideSchema = z.object({
    title: z.string().min(3).max(60).default('Visual Overview').meta({
        description: "Slide title",
    }),
    description: z.string().min(20).max(300).default('A detailed description of the topic being discussed. This text provides context and explanation for the accompanying image.').meta({
        description: "Main description text for the slide. Can be longer since the layout is split between text and image.",
    }),
    image: ImageSchema.default({
        __image_url__: '',
        __image_prompt__: 'professional presentation illustration',
    }).meta({ description: "Supporting image for the slide" }),
})

export const Schema = imageSlideSchema
export type ImageSlideData = z.infer<typeof imageSlideSchema>

interface ImageSlideLayoutProps { data?: Partial<ImageSlideData> }

const ImageSlideLayout: React.FC<ImageSlideLayoutProps> = ({ data: slideData }) => {
    return (
        <>
            <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700&display=swap" rel="stylesheet" />
            <div
                className="w-full rounded-sm max-w-[1280px] shadow-lg max-h-[720px] aspect-video relative z-20 mx-auto overflow-hidden flex"
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

                {/* Left: Text */}
                <div className="w-[50%] flex flex-col justify-center px-[52px] pt-[60px] pb-[40px]">
                    <h1
                        className="font-bold mb-4"
                        style={{ fontSize: '42.7px', letterSpacing: '-1.6px', lineHeight: '1.1', color: 'var(--background-text, #002BB2)' }}
                    >
                        {slideData?.title || 'Visual Overview'}
                    </h1>
                    <p style={{ fontSize: '16px', lineHeight: '1.7', color: 'var(--background-text, #002BB2)', opacity: 0.7 }}>
                        {slideData?.description || ''}
                    </p>
                </div>

                {/* Right: Image */}
                <div className="w-[50%] p-[20px] flex items-center justify-center">
                    {slideData?.image?.__image_url__ ? (
                        <img
                            src={slideData.image.__image_url__}
                            alt={slideData.image.__image_prompt__ || slideData?.title || ''}
                            className="max-w-full max-h-full rounded-lg object-contain"
                        />
                    ) : (
                        <div className="w-full aspect-video rounded-lg flex items-center justify-center" style={{ background: 'var(--card-color, #F7F8FF)' }}>
                            <span style={{ fontSize: '14px', color: 'var(--background-text, #002BB2)', opacity: 0.3 }}>Image</span>
                        </div>
                    )}
                </div>
            </div>
        </>
    )
}

export default ImageSlideLayout
