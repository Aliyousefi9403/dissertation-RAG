export const tokens = {
  colors: {
    bg: { void: '#050810', canvas: '#0A1220', elevated: '#101A2E' },
    border: {
      subtle: 'rgba(74, 159, 255, 0.08)',
      default: 'rgba(74, 159, 255, 0.15)',
      strong: 'rgba(74, 159, 255, 0.30)',
    },
    text: { primary: '#E8ECF3', secondary: '#8892A6', tertiary: '#4A5468' },
    accent: {
      primary: '#4A9FFF',
      active: '#00E5FF',
      warning: '#FFB84A',
      danger: '#FF4A6B',
      success: '#00FFA3',
    },
    glow: {
      primary: '0 0 40px rgba(74, 159, 255, 0.4)',
      active: '0 0 60px rgba(0, 229, 255, 0.5)',
    },
  },
  spacing: { xs: '4px', sm: '8px', md: '12px', base: '16px', lg: '24px', xl: '32px', '2xl': '48px', '3xl': '64px', '4xl': '96px' },
  fontSize: { '2xs': '10px', xs: '12px', sm: '14px', base: '16px', lg: '20px', xl: '28px', '2xl': '40px', '3xl': '56px' },
  motion: {
    duration: { fast: '150ms', standard: '250ms', slow: '400ms', emphasis: '600ms' },
    easing: {
      out: 'cubic-bezier(0.16, 1, 0.3, 1)',
      inout: 'cubic-bezier(0.65, 0, 0.35, 1)',
      spring: 'cubic-bezier(0.5, 1.5, 0.5, 1)',
    },
  },
} as const
