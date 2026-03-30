import React from 'react'
import * as z from "zod";
import { IconSchema, ImageSchema } from '../defaultSchemes';

export const layoutId = 'zachet-bullets-slide'
export const layoutName = 'Bullets with Image'
export const layoutDescription = 'A content slide with a title, bullet points on the left, and a supporting image on the right. Best for presenting key points, features, or steps with a visual.'

const bulletsSlideSchema = z.object({
    title: z.string().min(3).max(60).default('Key Points').meta({
        description: "Slide title",
    }),
    bullets: z.array(z.object({
        icon: IconSchema.default({
            __icon_url__: '',
            __icon_query__: 'checkmark',
        }).meta({ description: "Icon for the bullet point" }),
        heading: z.string().min(2).max(40).meta({
            description: "Short heading for the bullet",
        }),
        text: z.string().min(10).max(100).meta({
            description: "Description text for the bullet point",
        }),
    })).min(2).max(4).default([
        { icon: { __icon_url__: '', __icon_query__: 'target' }, heading: 'First Point', text: 'Description of the first key point in this section.' },
        { icon: { __icon_url__: '', __icon_query__: 'chart' }, heading: 'Second Point', text: 'Description of the second key point in this section.' },
        { icon: { __icon_url__: '', __icon_query__: 'lightbulb' }, heading: 'Third Point', text: 'Description of the third key point in this section.' },
    ]).meta({ description: "List of bullet points to display" }),
    image: ImageSchema.default({
        __image_url__: '',
        __image_prompt__: 'professional presentation visual',
    }).meta({ description: "Supporting image for the slide" }),
})

export const Schema = bulletsSlideSchema
export type BulletsSlideData = z.infer<typeof bulletsSlideSchema>

interface BulletsSlideLayoutProps { data?: Partial<BulletsSlideData> }

const BulletsSlideLayout: React.FC<BulletsSlideLayoutProps> = ({ data: slideData }) => {
    const bullets = slideData?.bullets || []

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

                {/* Left: Content */}
                <div className="w-[55%] flex flex-col justify-center px-[52px] pt-[60px] pb-[40px]">
                    <h1
                        className="font-bold mb-6"
                        style={{ fontSize: '42.7px', letterSpacing: '-1.6px', lineHeight: '1.1', color: 'var(--background-text, #002BB2)' }}
                    >
                        {slideData?.title || 'Key Points'}
                    </h1>
                    <div className="flex flex-col gap-[15px]">
                        {bullets.map((bullet, i) => (
                            <div
                                key={i}
                                className="flex items-start gap-4 p-4 rounded-[3.4px]"
                                style={{ background: 'var(--card-color, #F7F8FF)', borderLeft: '4px solid var(--stroke, #4C68DF)' }}
                            >
                                <div
                                    className="w-[40px] h-[40px] rounded-full flex items-center justify-center flex-shrink-0"
                                    style={{ border: '1.3px solid var(--stroke, #4C68DF)', background: 'var(--primary-color, #F7F8FF)' }}
                                >
                                    {bullet.icon?.__icon_url__ ? (
                                        <img src={bullet.icon.__icon_url__} alt="" className="w-5 h-5" />
                                    ) : (
                                        <span className="text-xs font-bold" style={{ color: 'var(--primary-color, #1F4CD9)' }}>{i + 1}</span>
                                    )}
                                </div>
                                <div>
                                    <div className="font-bold" style={{ fontSize: '17.5px', color: 'var(--background-text, #002BB2)' }}>
                                        {bullet.heading}
                                    </div>
                                    <div style={{ fontSize: '15.3px', lineHeight: '1.5', color: 'var(--background-text, #002BB2)', opacity: 0.7, marginTop: '2px' }}>
                                        {bullet.text}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Right: Image */}
                <div className="w-[45%] p-[20px] flex items-center justify-center">
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

export default BulletsSlideLayout
