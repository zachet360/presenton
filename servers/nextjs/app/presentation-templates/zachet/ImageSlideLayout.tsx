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
    }).meta({
        description: "Supporting image for the slide",
    }),
})

export const Schema = imageSlideSchema

export type ImageSlideData = z.infer<typeof imageSlideSchema>

interface ImageSlideLayoutProps {
    data?: Partial<ImageSlideData>
}

const ImageSlideLayout: React.FC<ImageSlideLayoutProps> = ({ data: slideData }) => {
    return (
        <div
            className="w-full rounded-sm max-w-[1280px] shadow-lg max-h-[720px] aspect-video relative z-20 mx-auto overflow-hidden flex"
            style={{
                fontFamily: 'var(--heading-font-family, Poppins)',
                background: 'var(--background-color, #ffffff)',
            }}
        >
            {((slideData as any)?.__companyName__ || (slideData as any)?._logo_url__) && (
                <div className="absolute top-0 left-0 right-0 px-12 pt-4 z-10">
                    <div className="flex items-center gap-1">
                        {(slideData as any)?._logo_url__ && <img src={(slideData as any)?._logo_url__} alt="logo" className="w-6 h-6" />}
                        {(slideData as any)?.__companyName__ && <span className="text-sm font-semibold" style={{ color: 'var(--background-text, #111827)' }}>{(slideData as any)?.__companyName__}</span>}
                    </div>
                </div>
            )}

            {/* Left: Text */}
            <div className="w-1/2 flex flex-col justify-center px-12 pt-10 pb-10">
                <h2
                    className="text-4xl font-bold mb-4"
                    style={{ color: 'var(--background-text, #111827)' }}
                >
                    {slideData?.title || 'Visual Overview'}
                </h2>
                <div className="w-16 h-1 mb-4" style={{ background: 'var(--primary-color, #9333ea)' }} />
                <p
                    className="text-base leading-relaxed"
                    style={{ color: 'var(--background-text, #4b5563)' }}
                >
                    {slideData?.description || ''}
                </p>
            </div>

            {/* Right: Image */}
            <div className="w-1/2 p-6 flex items-center justify-center">
                <div className="w-full h-full rounded-xl overflow-hidden">
                    {slideData?.image?.__image_url__ ? (
                        <img
                            src={slideData.image.__image_url__}
                            alt={slideData.image.__image_prompt__ || slideData?.title || ''}
                            className="w-full h-full object-cover"
                        />
                    ) : (
                        <div className="w-full h-full flex items-center justify-center" style={{ background: 'var(--card-color, #f3f4f6)' }}>
                            <span className="text-sm" style={{ color: 'var(--background-text, #9ca3af)' }}>Image</span>
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}

export default ImageSlideLayout
