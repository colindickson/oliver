import { createContext, useContext, useEffect, useState } from 'react'

const MOBILE_UA_REGEX = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i
const MOBILE_BREAKPOINT = 768

function detectMobile(): boolean {
  const byUA = MOBILE_UA_REGEX.test(navigator.userAgent)
  const byWidth = window.matchMedia(`(max-width: ${MOBILE_BREAKPOINT}px)`).matches
  return byUA || byWidth
}

const MobileContext = createContext<boolean>(false)

export function MobileProvider({ children }: { children: React.ReactNode }) {
  const [isMobile, setIsMobile] = useState<boolean>(detectMobile)

  useEffect(() => {
    const mq = window.matchMedia(`(max-width: ${MOBILE_BREAKPOINT}px)`)
    const handler = () => setIsMobile(detectMobile())
    mq.addEventListener('change', handler)
    return () => mq.removeEventListener('change', handler)
  }, [])

  return (
    <MobileContext.Provider value={isMobile}>
      {children}
    </MobileContext.Provider>
  )
}

export const useMobile = () => useContext(MobileContext)
