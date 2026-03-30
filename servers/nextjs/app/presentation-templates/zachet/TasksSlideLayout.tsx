import React from 'react'
import * as z from "zod";

export const layoutId = 'zachet-tasks-slide'
export const layoutName = 'Research Tasks'
export const layoutDescription = 'A slide listing the specific tasks/objectives of the research project. Each task is a numbered item describing a concrete step toward the research goal.'

const tasksSlideSchema = z.object({
    title: z.string().min(3).max(30).default('Задачи').meta({
        description: "Slide title, typically 'Задачи' or 'Задачи исследования'",
    }),
    tasks: z.array(
        z.string().min(10).max(150).meta({
            description: "A specific research task or objective",
        })
    ).min(3).max(6).default([
        'First research task',
        'Second research task',
        'Third research task',
    ]).meta({
        description: "Numbered list of research tasks/objectives",
    }),
})

export const Schema = tasksSlideSchema
export type TasksSlideData = z.infer<typeof tasksSlideSchema>

interface TasksSlideLayoutProps { data?: Partial<TasksSlideData> }

const TasksSlideLayout: React.FC<TasksSlideLayoutProps> = ({ data: slideData }) => {
    const tasks = slideData?.tasks || []

    return (
        <>
            <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700&display=swap" rel="stylesheet" />
            <div
                className="w-full rounded-sm max-w-[1280px] shadow-lg max-h-[720px] aspect-video relative z-20 mx-auto overflow-hidden flex flex-col"
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

                <div className="flex-1 flex px-[72px] pt-[60px] pb-[40px] gap-[60px]">
                    {/* Left: Title */}
                    <div className="w-[35%] flex flex-col justify-center">
                        <h1
                            className="font-bold"
                            style={{ fontSize: '42.7px', letterSpacing: '-1.6px', lineHeight: '1.1', color: 'var(--background-text, #002BB2)' }}
                        >
                            {slideData?.title || 'Задачи'}
                        </h1>
                        <div className="w-[60px] h-[4px] rounded-full mt-4" style={{ background: 'var(--primary-color, #1F4CD9)' }} />
                    </div>

                    {/* Right: Numbered tasks */}
                    <div className="w-[65%] flex flex-col justify-center gap-[16px]">
                        {tasks.map((task, i) => (
                            <div
                                key={i}
                                className="flex items-start gap-4 p-4 rounded"
                                style={{ background: 'var(--card-color, #F7F8FF)', borderLeft: '4px solid var(--stroke, #4C68DF)' }}
                            >
                                <div
                                    className="w-[36px] h-[36px] rounded-full flex items-center justify-center flex-shrink-0"
                                    style={{ background: 'var(--primary-color, #1F4CD9)' }}
                                >
                                    <span className="text-sm font-bold" style={{ color: 'var(--primary-text, #FFFFFF)' }}>{i + 1}</span>
                                </div>
                                <p className="pt-1.5" style={{ fontSize: '15.3px', lineHeight: '1.5', color: 'var(--background-text, #002BB2)', opacity: 0.8 }}>
                                    {task}
                                </p>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </>
    )
}

export default TasksSlideLayout
