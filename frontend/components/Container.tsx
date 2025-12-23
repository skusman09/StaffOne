import React from 'react'

interface ContainerProps {
    children: React.ReactNode
    className?: string
}

export default function Container({ children, className = '' }: ContainerProps) {
    return (
        <div className={`mx-auto px-4 sm:px-6 lg:px-8 xl:px-12 max-w-full lg:max-w-7xl xl:max-w-[90vw] 2xl:max-w-[1800px] ${className}`}>
            {children}
        </div>
    )
}
