import type { ComponentPropsWithoutRef } from 'react'

import { cn } from '@/lib/utils'

type SkeletonProps = ComponentPropsWithoutRef<'div'>

const Skeleton = ({ className, ...rest }: SkeletonProps) => {
  return (
    <div
      className={cn(
        'animate-pulse rounded-md border border-slate-200/70 bg-slate-100',
        className
      )}
      {...rest}
    />
  )
}

export default Skeleton


