/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        'sans': ['Roboto', 'system-ui', 'sans-serif'],
      },
      colors: {
        'neon-purple': '#764ba2',
        'neon-blue': '#667eea',
        'neon-pink': '#f093fb',
        'neon-red': '#f5576c',
        'neon-cyan': '#4facfe',
        'neon-teal': '#00f2fe',
        'neon-orange': '#fa709a',
        'neon-yellow': '#fee140',
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-conic': 'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
        'gradient-primary': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        'gradient-secondary': 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
        'gradient-tertiary': 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
        'gradient-quaternary': 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
      },
      animation: {
        'float': 'float 3s ease-in-out infinite',
        'glow': 'glow 2s ease-in-out infinite',
        'gradient': 'gradient 3s ease infinite',
        'pulse-neon': 'pulse-neon 2s ease-in-out infinite',
        'rotate-3d': 'rotate-3d 10s linear infinite',
        'morph': 'morph 8s ease-in-out infinite',
        'glitch': 'glitch 3s ease-in-out infinite',
        'particle': 'particle 15s linear infinite',
        'wave': 'wave 10s ease-in-out infinite',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-20px)' },
        },
        glow: {
          '0%, 100%': { boxShadow: '0 0 20px rgba(99, 102, 241, 0.3)' },
          '50%': { boxShadow: '0 0 40px rgba(99, 102, 241, 0.8)' },
        },
        gradient: {
          '0%': { backgroundPosition: '0% 50%' },
          '50%': { backgroundPosition: '100% 50%' },
          '100%': { backgroundPosition: '0% 50%' },
        },
        'pulse-neon': {
          '0%, 100%': { 
            opacity: '1',
            textShadow: '0 0 10px rgba(102, 126, 234, 0.8), 0 0 20px rgba(102, 126, 234, 0.6)'
          },
          '50%': { 
            opacity: '0.8',
            textShadow: '0 0 20px rgba(102, 126, 234, 1), 0 0 40px rgba(102, 126, 234, 0.8)'
          },
        },
        'rotate-3d': {
          '0%': { transform: 'rotateX(0deg) rotateY(0deg)' },
          '100%': { transform: 'rotateX(360deg) rotateY(360deg)' },
        },
        morph: {
          '0%, 100%': { borderRadius: '60% 40% 30% 70%/60% 30% 70% 40%' },
          '50%': { borderRadius: '30% 60% 70% 40%/50% 60% 30% 60%' },
        },
        glitch: {
          '0%, 100%': { transform: 'translate(0)' },
          '20%': { transform: 'translate(-2px, 2px)' },
          '40%': { transform: 'translate(-2px, -2px)' },
          '60%': { transform: 'translate(2px, 2px)' },
          '80%': { transform: 'translate(2px, -2px)' },
        },
        particle: {
          '0%': { transform: 'translateY(0) translateX(0) scale(1)', opacity: '1' },
          '100%': { transform: 'translateY(-100vh) translateX(100px) scale(0)', opacity: '0' },
        },
        wave: {
          '0%, 100%': { transform: 'translateX(-100%)' },
          '50%': { transform: 'translateX(100%)' },
        },
      },
      backdropBlur: {
        xs: '2px',
        '4xl': '72px',
      },
      boxShadow: {
        'neon': '0 0 30px rgba(102, 126, 234, 0.8)',
        'neon-lg': '0 0 60px rgba(102, 126, 234, 1)',
        '3d': '0 20px 40px -10px rgba(0, 0, 0, 0.3)',
        '3d-hover': '0 30px 60px -15px rgba(0, 0, 0, 0.4)',
        'inner-glow': 'inset 0 0 30px rgba(255, 255, 255, 0.2)',
      },
      transformOrigin: {
        '3d': '50% 50% 0',
      },
      perspective: {
        '3d': '1000px',
      },
    },
  },
  plugins: [],
}