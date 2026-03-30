import React from 'react'
import * as z from "zod";
import { IconSchema } from '../defaultSchemes';

export const layoutId = 'zachet-bullets-slide'
export const layoutName = 'Bullets'
export const layoutDescription = 'A content slide with a title, description, and a list of bullet points with icons. Best for presenting key points, features, or steps.'

const bulletsSlideSchema = z.object({
    title: z.string().min(3).max(60).default('Key Points').meta({
        description: "Slide title",
    }),
    description: z.string().min(10).max(180).default('An overview of the main points covered in this section of the presentation.').meta({
        description: "Brief introductory description for the slide",
    }),
    bullets: z.array(z.object({
        icon: IconSchema.default({
            __icon_url__: '',
            __icon_query__: 'checkmark',
        }).meta({ description: "Icon for the bullet point" }),
        heading: z.string().min(2).max(40).meta({
            description: "Short heading for the bullet",
        }),
        text: z.string().min(10).max(120).meta({
            description: "Description text for the bullet point",
        }),
    })).min(2).max(5).default([
        { icon: { __icon_url__: '', __icon_query__: 'target' }, heading: 'First Point', text: 'Description of the first key point in this section.' },
        { icon: { __icon_url__: '', __icon_query__: 'chart' }, heading: 'Second Point', text: 'Description of the second key point in this section.' },
        { icon: { __icon_url__: '', __icon_query__: 'lightbulb' }, heading: 'Third Point', text: 'Description of the third key point in this section.' },
    ]).meta({
        description: "List of bullet points to display",
    }),
})

export const Schema = bulletsSlideSchema

export type BulletsSlideData = z.infer<typeof bulletsSlideSchema>

interface BulletsSlideLayoutProps {
    data?: Partial<BulletsSlideData>
}

const BulletsSlideLayout: React.FC<BulletsSlideLayoutProps> = ({ data: slideData }) => {
    const bullets = slideData?.bullets || []

    return (
        <div
            className="w-full rounded-sm max-w-[1280px] shadow-lg max-h-[720px] aspect-video relative z-20 mx-auto overflow-hidden flex flex-col"
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

            <div className="flex-1 flex flex-col justify-center px-12 pt-10 pb-10">
                <h2
                    className="text-4xl font-bold mb-2"
                    style={{ color: 'var(--background-text, #111827)' }}
                >
                    {slideData?.title || 'Key Points'}
                </h2>
                <p
                    className="text-base mb-6 max-w-2xl"
                    style={{ color: 'var(--background-text, #6b7280)' }}
                >
                    {slideData?.description || ''}
                </p>

                <div className={`grid gap-4 ${bullets.length <= 3 ? 'grid-cols-1' : 'grid-cols-2'}`}>
                    {bullets.map((bullet, i) => (
                        <div key={i} className="flex items-start gap-3 p-3 rounded-lg" style={{ background: 'var(--card-color, #f9fafb)' }}>
                            <div
                                className="w-8 h-8 rounded flex items-center justify-center flex-shrink-0 mt-0.5"
                                style={{ background: 'var(--primary-color, #9333ea)' }}
                            >
                                {bullet.icon?.__icon_url__ ? (
                                    <img src={bullet.icon.__icon_url__} alt="" className="w-5 h-5" />
                                ) : (
                                    <span className="text-xs font-bold" style={{ color: 'var(--primary-text, #ffffff)' }}>{i + 1}</span>
                                )}
                            </div>
                            <div className="min-w-0">
                                <div className="text-sm font-semibold" style={{ color: 'var(--background-text, #111827)' }}>
                                    {bullet.heading}
                                </div>
                                <div className="text-xs leading-relaxed mt-0.5" style={{ color: 'var(--background-text, #6b7280)' }}>
                                    {bullet.text}
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    )
}

export default BulletsSlideLayout
