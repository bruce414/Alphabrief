import { useEffect, useRef, useState } from 'react'

/**
 * True when vertical scroll exceeds `threshold` (px).
 * Updates at most once per animation frame for scroll events.
 */
export function useNavDocked(threshold = 32) {
  const [docked, setDocked] = useState(false)
  const rafRef = useRef<number | null>(null)
  const dockedRef = useRef(false)

  useEffect(() => {
    const readScroll = () => {
      return window.scrollY > threshold
    }

    const apply = () => {
      const next = readScroll()
      if (next !== dockedRef.current) {
        dockedRef.current = next
        setDocked(next)
      }
    }

    const onScroll = () => {
      if (rafRef.current != null) return
      rafRef.current = window.requestAnimationFrame(() => {
        rafRef.current = null
        apply()
      })
    }

    apply()
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => {
      window.removeEventListener('scroll', onScroll)
      if (rafRef.current != null) {
        window.cancelAnimationFrame(rafRef.current)
        rafRef.current = null
      }
    }
  }, [threshold])

  return docked
}
