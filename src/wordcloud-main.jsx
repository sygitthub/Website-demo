import React from 'react';
import { createRoot } from 'react-dom/client';
import SphereWordCloud from './components/SphereWordCloud.jsx';

const rootEl = document.getElementById('sphere-wordcloud-root');
if (rootEl) {
  createRoot(rootEl).render(React.createElement(SphereWordCloud));
}
