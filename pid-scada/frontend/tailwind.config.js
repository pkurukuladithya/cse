export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        accent: '#00c8e8',
        accentDim: '#0090a8',
        green: '#00e5a0',
        amber: '#f5a623',
        red: '#f03e3e',
        purple: '#9b6dff',
        bgPanel: '#0c1420',
        bgSurface: '#16243a',
        border: 'rgba(0,200,232,0.12)',
      },
      boxShadow: {
        panel: '0 20px 40px rgba(0,0,0,0.12)',
      },
    },
  },
  plugins: [],
};
