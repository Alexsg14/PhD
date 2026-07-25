# 📖 Preimpresión PDF – Visualizador de Pliegos (PDF Book Spread Visualizer)

A modern, high-performance web utility built with **React**, **Vite**, **Tailwind CSS**, and **PDF.js** for previewing multi-page PDF documents in physical book-spread format prior to printing and binding.

---

## ✨ Features

- **Facing Pages / Book Spread View (Vista Libro):**
  - Displays PDF documents as open book spreads (Portada / Cover page 1 on the right, even pages on left, odd pages on right).
  - Renders realistic spine fold gradients and 3D page drop-shadows.
- **Single Page View (Vista Individual):**
  - Displays pages sequentially for inspecting full bleed, crop marks, and margins.
- **Paper Size Simulation:**
  - Simulates standard paper formats (**A4**, **A5**, **Carta/Letter**, **Legal**, or **Original Native PDF Ratio**).
  - Highlights aspect-ratio mismatches between the source PDF and selected print target.
- **High-Performance Lazy Loading:**
  - Uses `IntersectionObserver` to render canvas viewports only when scrolled into view, keeping memory usage minimal even on multi-hundred page documents.
- **Standalone Offline Variant (`visor-pdf.html`):**
  - Includes a single-file standalone HTML version utilizing React UMD, Babel Standalone, and Tailwind CDN—executable directly in any web browser without needing Node.js or build tools.

---

## 📁 Directory Structure

```
_Visor_PDF_/
├── src/
│   ├── App.jsx            # Main React component (Toolbars, Spreads calculation, Canvas PDF rendering)
│   ├── main.jsx           # Application entry point
│   └── index.css          # Tailwind CSS directives
├── public/                # Static assets
├── index.html             # Vite HTML entry point
├── visor-pdf.html         # Standalone single-file HTML version (React UMD + Babel + Tailwind CDN)
├── package.json           # Dependencies & scripts
├── vite.config.js         # Vite configuration
└── README.md              # Module documentation
```

---

## 🚀 Quick Start

### Development Server

1. Navigate to the directory and install dependencies:
   ```bash
   cd _Visor_PDF_
   npm install
   ```

2. Launch local development server:
   ```bash
   npm run dev
   ```

3. Open your browser at `http://localhost:5173`.

### Production Build

```bash
npm run build
```

The optimized static bundle will be output to `dist/`.

---

## 🌐 Standalone Browser Usage

To run the visualizer without starting a local server or installing Node.js:
- Open [`visor-pdf.html`](file:///home/ciqus/GIT/Github_Personal/PhD/_Visor_PDF_/visor-pdf.html) directly in any modern browser.
