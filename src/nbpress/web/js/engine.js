/**
 * nbpress Engine · In-Browser Notebook Parser & Typst Markup Generator
 * 100% Client-Side · Private · Instantaneous
 */

(function (window) {
  'use strict';

  // Fallback math symbol converter when KaTeX is not loaded
  function fallbackMathSymbolReplace(tex) {
    if (!tex) return '';

    let res = tex
      .replace(/\\hbar\b/g, 'ℏ')
      .replace(/\\partial\b/g, '∂')
      .replace(/\\nabla\b/g, '∇')
      .replace(/\\infty\b/g, '∞')
      .replace(/\\times\b/g, '×')
      .replace(/\\cdot\b/g, '·')
      .replace(/\\pm\b/g, '±')
      .replace(/\\neq\b/g, '≠')
      .replace(/\\leq\b/g, '≤')
      .replace(/\\geq\b/g, '≥')
      .replace(/\\approx\b/g, '≈')
      .replace(/\\in\b/g, '∈')
      .replace(/\\sum\b/g, '∑')
      .replace(/\\int\b/g, '∫')
      .replace(/\\prod\b/g, '∏')
      .replace(/\\sqrt\{([^}]+)\}/g, '√($1)')
      .replace(/\\frac\{([^}]+)\}\{([^}]+)\}/g, '($1)/($2)')
      .replace(/\\mathbf\{([^}]+)\}/g, '$1')
      .replace(/\\boldsymbol\{([^}]+)\}/g, '$1')
      .replace(/\\text\{([^}]+)\}/g, '$1')
      .replace(/\\operatorname\{([^}]+)\}/g, '$1')
      .replace(/\\quad\b/g, '  ')
      .replace(/\\qquad\b/g, '    ');

    // Greek letters
    const greek = {
      'alpha': 'α', 'beta': 'β', 'gamma': 'γ', 'delta': 'δ', 'epsilon': 'ε',
      'zeta': 'ζ', 'eta': 'η', 'theta': 'θ', 'iota': 'ι', 'kappa': 'κ',
      'lambda': 'λ', 'mu': 'μ', 'nu': 'ν', 'xi': 'ξ', 'pi': 'π',
      'rho': 'ρ', 'sigma': 'σ', 'tau': 'τ', 'upsilon': 'υ', 'phi': 'φ',
      'chi': 'χ', 'psi': 'ψ', 'omega': 'ω',
      'Gamma': 'Γ', 'Delta': 'Δ', 'Theta': 'Θ', 'Lambda': 'Λ', 'Xi': 'Ξ',
      'Pi': 'Π', 'Sigma': 'Σ', 'Upsilon': 'Υ', 'Phi': 'Φ', 'Psi': 'Ψ', 'Omega': 'Ω'
    };
    for (const [name, sym] of Object.entries(greek)) {
      res = res.replace(new RegExp('\\\\' + name + '\\b', 'g'), sym);
    }

    // Common superscripts & subscripts
    res = res.replace(/\^0\b/g, '⁰').replace(/\^1\b/g, '¹').replace(/\^2\b/g, '²').replace(/\^3\b/g, '³')
      .replace(/\^\{0\}/g, '⁰').replace(/\^\{1\}/g, '¹').replace(/\^\{2\}/g, '²').replace(/\^\{3\}/g, '³')
      .replace(/\^k\b/g, 'ᵏ').replace(/\^T\b/g, 'ᵀ')
      .replace(/_0\b/g, '₀').replace(/_1\b/g, '₁').replace(/_2\b/g, '₂').replace(/_3\b/g, '₃')
      .replace(/_\{0\}/g, '₀').replace(/_\{1\}/g, '₁').replace(/_\{2\}/g, '₂').replace(/_\{3\}/g, '₃')
      .replace(/_\{ijk\}/g, 'ᵢⱼₖ')
      .replace(/\^\\mu\b/g, 'ᵘ').replace(/_\\mu\b/g, 'ᵤ')
      .replace(/\^\\nu\b/g, 'ᵛ').replace(/_\\nu\b/g, 'ᵥ');

    return res;
  }

  const NbpressEngine = {
    /**
     * Parses .ipynb JSON file content into a structured notebook document.
     */
    parseNotebook: function (input, fileName) {
      let data = typeof input === 'string' ? JSON.parse(input) : input;
      fileName = fileName || 'notebook.ipynb';

      const nb = {
        fileName: fileName,
        title: this.detectTitle(data, fileName),
        authors: this.detectAuthors(data),
        language: (data.metadata && data.metadata.language_info && data.metadata.language_info.name) || 'python',
        kernel: (data.metadata && data.metadata.kernelspec && data.metadata.kernelspec.display_name) || 'Python 3',
        cells: [],
        stats: {
          totalCells: 0,
          markdownCells: 0,
          codeCells: 0,
          rawCells: 0,
          imagesCount: 0,
          tablesCount: 0,
          errorsCount: 0,
          slidesCount: 0
        },
        raw: data
      };

      const rawCells = data.cells || [];
      nb.stats.totalCells = rawCells.length;

      let currentSlideIndex = 0;

      rawCells.forEach((c, idx) => {
        const cell = {
          index: idx,
          id: c.id || ('cell_' + idx),
          type: c.cell_type || 'markdown',
          source: Array.isArray(c.source) ? c.source.join('') : (c.source || ''),
          executionCount: c.execution_count || null,
          outputs: [],
          isSlideStarter: false,
          slideTitle: ''
        };

        // Detect slide boundary
        const slideMeta = c.metadata && c.metadata.slideshow && c.metadata.slideshow.slide_type;
        if (slideMeta === 'slide' || slideMeta === 'subslide') {
          cell.isSlideStarter = true;
        } else if (cell.type === 'markdown') {
          const firstLine = cell.source.trim().split('\n')[0] || '';
          if (firstLine.startsWith('# ') || firstLine.startsWith('## ') || firstLine.startsWith('### ')) {
            cell.isSlideStarter = true;
          }
        }

        if (cell.isSlideStarter) {
          currentSlideIndex++;
          nb.stats.slidesCount++;
          const match = cell.source.match(/^#{1,3}\s+(.+)$/m);
          cell.slideTitle = match ? match[1].replace(/[*_`]/g, '').trim() : `Slide ${currentSlideIndex}`;
        }

        if (cell.type === 'markdown') {
          nb.stats.markdownCells++;
        } else if (cell.type === 'code') {
          nb.stats.codeCells++;
        } else {
          nb.stats.rawCells++;
        }

        // Process outputs
        if (c.outputs && Array.isArray(c.outputs)) {
          c.outputs.forEach(out => {
            const parsedOut = {
              type: out.output_type,
              text: '',
              html: '',
              images: [],
              hasImage: false,
              hasTable: false,
              isError: out.output_type === 'error'
            };

            if (parsedOut.isError) {
              nb.stats.errorsCount++;
              parsedOut.text = (out.traceback || []).join('\n') || (out.ename + ': ' + out.evalue);
            } else if (out.output_type === 'stream') {
              parsedOut.text = Array.isArray(out.text) ? out.text.join('') : (out.text || '');
            } else if (out.output_type === 'execute_result' || out.output_type === 'display_data') {
              const dataObj = out.data || {};

              // Images
              if (dataObj['image/png']) {
                parsedOut.images.push('data:image/png;base64,' + dataObj['image/png']);
                parsedOut.hasImage = true;
                nb.stats.imagesCount++;
              }
              if (dataObj['image/jpeg']) {
                parsedOut.images.push('data:image/jpeg;base64,' + dataObj['image/jpeg']);
                parsedOut.hasImage = true;
                nb.stats.imagesCount++;
              }
              if (dataObj['image/svg+xml']) {
                const svgStr = Array.isArray(dataObj['image/svg+xml']) ? dataObj['image/svg+xml'].join('') : dataObj['image/svg+xml'];
                parsedOut.images.push('data:image/svg+xml;utf8,' + encodeURIComponent(svgStr));
                parsedOut.hasImage = true;
                nb.stats.imagesCount++;
              }

              // HTML tables
              if (dataObj['text/html']) {
                parsedOut.html = Array.isArray(dataObj['text/html']) ? dataObj['text/html'].join('') : dataObj['text/html'];
                if (parsedOut.html.includes('<table')) {
                  parsedOut.hasTable = true;
                  nb.stats.tablesCount++;
                }
              }

              // Text fallback
              if (dataObj['text/plain']) {
                parsedOut.text = Array.isArray(dataObj['text/plain']) ? dataObj['text/plain'].join('') : dataObj['text/plain'];
              }
            }

            cell.outputs.push(parsedOut);
          });
        }

        nb.cells.push(cell);
      });

      if (nb.stats.slidesCount === 0) {
        nb.stats.slidesCount = Math.max(1, nb.stats.markdownCells);
      }

      return nb;
    },

    detectTitle: function (data, fileName) {
      if (data.metadata && data.metadata.title) {
        return data.metadata.title;
      }
      const cells = data.cells || [];
      for (let i = 0; i < cells.length; i++) {
        const c = cells[i];
        if (c.cell_type === 'markdown') {
          const src = Array.isArray(c.source) ? c.source.join('') : (c.source || '');
          const match = src.match(/^#\s+(.+)$/m);
          if (match && match[1]) {
            return match[1].replace(/[*_`]/g, '').trim();
          }
        }
      }
      return fileName.replace(/\.ipynb$/i, '').replace(/[-_]/g, ' ');
    },

    detectAuthors: function (data) {
      if (data.metadata && data.metadata.authors) {
        if (Array.isArray(data.metadata.authors)) {
          return data.metadata.authors.map(a => typeof a === 'string' ? a : (a.name || '')).filter(Boolean);
        }
      }
      return [];
    },

    /**
     * Groups cells into logical slides for Slides & Handout modes.
     */
    buildSlidesList: function (nb) {
      const slides = [];
      let currentTitle = nb.title;
      let currentCells = [];

      nb.cells.forEach((cell, idx) => {
        const isNew = cell.isSlideStarter && (idx > 0 || cell.type === 'markdown');
        if (isNew && currentCells.length > 0) {
          slides.push({
            index: slides.length + 1,
            title: currentTitle,
            cells: currentCells
          });
          currentCells = [];
          currentTitle = cell.slideTitle || `Slide ${slides.length + 1}`;
        } else if (cell.isSlideStarter) {
          currentTitle = cell.slideTitle || `Slide ${slides.length + 1}`;
        }
        currentCells.push(cell);
      });

      if (currentCells.length > 0) {
        slides.push({
          index: slides.length + 1,
          title: currentTitle,
          cells: currentCells
        });
      }

      if (!slides.length) {
        slides.push({
          index: 1,
          title: nb.title,
          cells: nb.cells
        });
      }

      return slides;
    },

    /**
     * Converts LaTeX / Markdown text to publication-grade styled HTML.
     * @param {string} text - Source text
     * @param {boolean} stripFirstHeading - If true, strips the leading H1/H2 (to prevent duplicating slide title)
     */
    formatMathAndMarkdown: function (text, stripFirstHeading) {
      if (!text) return '';

      let src = text.trim();

      // Clean LaTeX accents in Spanish/Galician text: \'{\i} -> í, \'e -> é, etc.
      src = src
        .replace(/\\'\s*\{\\i\}/g, 'í')
        .replace(/\\'\s*\{i\}/g, 'í')
        .replace(/\\'\s*i\b/g, 'í')
        .replace(/\\'\s*\{a\}/g, 'á')
        .replace(/\\'\s*a\b/g, 'á')
        .replace(/\\'\s*\{e\}/g, 'é')
        .replace(/\\'\s*e\b/g, 'é')
        .replace(/\\'\s*\{o\}/g, 'ó')
        .replace(/\\'\s*o\b/g, 'ó')
        .replace(/\\'\s*\{u\}/g, 'ú')
        .replace(/\\'\s*u\b/g, 'ú')
        .replace(/\\~\s*\{n\}/g, 'ñ')
        .replace(/\\~\s*n\b/g, 'ñ');

      // If requested, strip the first heading so it does not repeat under the slide title
      if (stripFirstHeading) {
        src = src.replace(/^(#{1,3})\s+[^\n]+\n*/m, '').trim();
      }

      if (!src) return '';

      // 1. Math block replacements using KaTeX if available
      const hasKatex = typeof window.katex !== 'undefined';

      // Process display math $$ ... $$
      src = src.replace(/\$\$([\s\S]*?)\$\$/g, function (match, eq) {
        const cleanEq = eq.trim();
        if (!cleanEq) return '';

        if (hasKatex) {
          try {
            const rendered = window.katex.renderToString(cleanEq, { displayMode: true, throwOnError: false });
            return `<div class="sheet-math-box">${rendered}</div>`;
          } catch (e) {
            console.warn('KaTeX display render error:', e);
          }
        }
        const fallback = fallbackMathSymbolReplace(cleanEq);
        return `<div class="sheet-math-box"><em>${fallback}</em></div>`;
      });

      // Process inline math $ ... $ (ignoring empty or escaped dollars)
      src = src.replace(/(?<!\\)\$([^\$\n]+?)(?<!\\)\$/g, function (match, eq) {
        const cleanEq = eq.trim();
        if (!cleanEq) return '';

        if (hasKatex) {
          try {
            const rendered = window.katex.renderToString(cleanEq, { displayMode: false, throwOnError: false });
            return rendered;
          } catch (e) {
            console.warn('KaTeX inline render error:', e);
          }
        }
        const fallback = fallbackMathSymbolReplace(cleanEq);
        return `<span style="font-family:'Newsreader',Georgia,serif; font-style:italic;">${fallback}</span>`;
      });

      // Escape basic HTML tags in prose
      let safe = src
        .replace(/&(?!(?:amp|lt|gt|quot|#\d+|#x[a-f\d]+);)/gi, '&amp;');

      // 2. Headings (Support all levels 1 to 6)
      safe = safe.replace(/^######\s+(.*$)/gim, '<h6 class="sheet-h6">$1</h6>');
      safe = safe.replace(/^#####\s+(.*$)/gim, '<h5 class="sheet-h5">$1</h5>');
      safe = safe.replace(/^####\s+(.*$)/gim, '<h4 class="sheet-h4">$1</h4>');
      safe = safe.replace(/^###\s+(.*$)/gim, '<h3 style="font-size:1.05rem; font-weight:700; margin-top:0.75rem; margin-bottom:0.35rem; color:#171717;">$1</h3>');
      safe = safe.replace(/^##\s+(.*$)/gim, '<h2 style="font-family:var(--font-serif-display); font-size:1.35rem; margin-top:0.9rem; margin-bottom:0.4rem; color:#171717;">$1</h2>');
      safe = safe.replace(/^#\s+(.*$)/gim, '<h1 class="sheet-title" style="margin-top:0.5rem; margin-bottom:0.5rem;">$1</h1>');

      // 3. Blockquotes
      safe = safe.replace(/^\>\s?(.*$)/gim, '<blockquote style="border-left:3px solid #c2410c; padding-left:0.8rem; margin:0.6rem 0; color:#52504b; font-style:italic;">$1</blockquote>');

      // 4. Bold, Italic & Code
      safe = safe.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
      safe = safe.replace(/\*([^*]+)\*/g, '<em>$1</em>');
      safe = safe.replace(/`([^`]+)`/g, '<code style="background:#f0ece3; padding:1px 4px; border-radius:3px; font-family:var(--font-mono); font-size:0.8em; color:#171717;">$1</code>');

      // 5. Links: [text](url) and reference labels [text]
      safe = safe.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener" style="color:#c2410c; text-decoration:underline;">$1</a>');
      safe = safe.replace(/\[([a-zA-Z0-9_-]+)\](?!\()/g, '<span style="color:#52504b; font-size:0.85em; background:#f0ece3; padding:0 3px; border-radius:2px;">[$1]</span>');

      // 6. Markdown Tables
      safe = safe.replace(/(\|.+?\|\n)+/g, function (match) {
        const lines = match.trim().split('\n');
        if (lines.length < 2) return match;
        let html = '<div style="overflow-x:auto; margin:0.6rem 0;"><table style="width:100%; border-collapse:collapse; font-size:0.78rem;">';
        lines.forEach((line, idx) => {
          if (idx === 1 && line.includes('---')) return;
          const cols = line.split('|').slice(1, -1);
          const tag = idx === 0 ? 'th' : 'td';
          html += '<tr>';
          cols.forEach(c => {
            const style = idx === 0
              ? 'border-bottom:1.5px solid #171717; padding:4px 8px; font-weight:bold; text-align:left;'
              : 'border-bottom:1px solid #e2ddd3; padding:4px 8px; text-align:left;';
            html += `<${tag} style="${style}">${c.trim()}</${tag}>`;
          });
          html += '</tr>';
        });
        html += '</table></div>';
        return html;
      });

      // 7. Paragraphs
      return safe.split(/\n\s*\n/).map(p => {
        const trimmed = p.trim();
        if (!trimmed) return '';
        if (trimmed.startsWith('<h') || trimmed.startsWith('<div') || trimmed.startsWith('<blockquote') || trimmed.startsWith('<table')) {
          return trimmed;
        }
        return `<p class="sheet-prose">${trimmed.replace(/\n/g, '<br>')}</p>`;
      }).filter(Boolean).join('');
    },

    /**
     * Generates simulated print pages for the preview canvas & browser print engine.
     */
    generateSheets: function (nb, config) {
      config = config || {};
      const layout = config.layout || 'document';
      const theme = config.theme || 'editorial';
      const gutter = config.gutter || 'none';
      const duplex = !!config.duplex;
      const holeGuides = !!config.holeGuides;
      const eco = !!config.eco;
      const noteStyle = config.handoutNoteStyle || 'lines';
      const handoutLayout = config.handoutLayout || '1-up';

      const sheets = [];

      const createSheet = (sheetNum, totalSheets) => {
        let isEven = sheetNum % 2 === 0;
        let gutterClass = '';
        if (gutter !== 'none') {
          if (duplex) {
            gutterClass = isEven ? 'has-gutter-right' : 'has-gutter-left';
          } else {
            gutterClass = 'has-gutter-left';
          }
        }

        return {
          pageNumber: sheetNum,
          totalCount: totalSheets,
          gutterClass: gutterClass,
          holeGuides: holeGuides,
          isSlide: layout === 'slides',
          headerText: `${config.titleOverride || nb.title} · nbpress ${theme}`,
          footerText: `Pág. ${sheetNum} de ${totalSheets}`,
          htmlContent: ''
        };
      };

      if (layout === 'document') {
        // --- Mode 1: Document (Academic Continuous Report) ---
        let contentChunks = [];

        nb.cells.forEach(cell => {
          if (cell.type === 'markdown') {
            const formatted = this.formatMathAndMarkdown(cell.source, false);
            if (formatted) contentChunks.push({ type: 'md', html: formatted, weight: Math.max(1, Math.ceil(cell.source.length / 300)) });
          } else if (cell.type === 'code' && config.showCode !== false) {
            const prompt = config.showPrompts !== false ? `<span class="sheet-code-prompt">In [${cell.executionCount || ' '}]:</span> ` : '';
            const codeHtml = `
              <div class="sheet-code-block" style="${eco ? 'background:#ffffff; border-color:#d5cfc2;' : ''}">
                ${prompt}${cell.source.replace(/</g, '&lt;').replace(/>/g, '&gt;')}
              </div>
            `;
            contentChunks.push({ type: 'code', html: codeHtml, weight: 2 });

            // Outputs
            cell.outputs.forEach(out => {
              if (out.hasImage && out.images.length) {
                out.images.forEach(imgSrc => {
                  contentChunks.push({
                    type: 'image',
                    html: `<div class="sheet-img-wrap" style="margin:0.5rem 0;"><img src="${imgSrc}" alt="Plot"></div>`,
                    weight: 4
                  });
                });
              } else if (out.hasTable && out.html) {
                contentChunks.push({
                  type: 'table',
                  html: `<div style="overflow-x:auto; margin:0.5rem 0;">${out.html}</div>`,
                  weight: 3
                });
              } else if (out.text && !out.isError) {
                contentChunks.push({
                  type: 'text',
                  html: `<div style="font-family:var(--font-mono); font-size:0.68rem; color:#52504b; background:#fcfbf9; padding:4px 8px; border-left:2px solid #a39f97; margin:0.35rem 0; white-space:pre-wrap;">${out.text.replace(/</g, '&lt;').replace(/>/g, '&gt;').slice(0, 300)}</div>`,
                  weight: 1
                });
              }
            });
          }
        });

        // Sheet 1: Editorial Cover Page (if enabled)
        if (config.cover !== false) {
          const coverSheet = createSheet(1, 1);
          coverSheet.htmlContent = `
            <div style="flex:1; display:flex; flex-direction:column; justify-content:center; align-items:flex-start; padding:3rem 0;">
              <div style="font-family:var(--font-mono); font-size:0.75rem; text-transform:uppercase; letter-spacing:0.15em; color:#c2410c; margin-bottom:1rem;">
                NBPRESS · EDITORIAL REPORT
              </div>
              <h1 style="font-family:var(--font-serif-display); font-size:2.4rem; font-weight:700; line-height:1.15; color:#171717; margin-bottom:1.5rem;">
                ${config.titleOverride || nb.title}
              </h1>
              <div style="width:60px; height:3px; background:#c2410c; margin-bottom:1.75rem;"></div>
              <div style="font-size:0.95rem; color:#52504b; line-height:1.6;">
                <strong>Notebook:</strong> ${nb.fileName}<br>
                <strong>Kernel:</strong> ${nb.kernel} (${nb.language})<br>
                ${nb.authors.length ? `<strong>Autores:</strong> ${nb.authors.join(', ')}<br>` : ''}
                <strong>Celdas:</strong> ${nb.stats.totalCells} (${nb.stats.codeCells} código, ${nb.stats.markdownCells} markdown)<br>
                <strong>Gráficos:</strong> ${nb.stats.imagesCount} figuras renderizadas
              </div>
            </div>
          `;
          sheets.push(coverSheet);
        }

        // Budget pages: ~6-8 weight units per page to avoid overflow
        let currentSheet = createSheet(sheets.length + 1, 1);
        let currentWeight = 0;

        contentChunks.forEach(chunk => {
          if (currentWeight + chunk.weight > 7 && currentSheet.htmlContent) {
            sheets.push(currentSheet);
            currentSheet = createSheet(sheets.length + 1, 1);
            currentWeight = 0;
          }
          currentSheet.htmlContent += `<div style="margin-bottom:0.75rem;">${chunk.html}</div>`;
          currentWeight += chunk.weight;
        });

        if (currentSheet.htmlContent) {
          sheets.push(currentSheet);
        }

      } else if (layout === 'slides') {
        // --- Mode 2: Slides (16:9 Presentation Deck) ---
        const slidesList = this.buildSlidesList(nb);

        slidesList.forEach((slide, idx) => {
          const sheet = createSheet(idx + 1, slidesList.length);
          sheet.isSlide = true;
          sheet.footerText = `${nb.title} · Diapositiva ${idx + 1} de ${slidesList.length}`;

          let bodyHtml = '';
          slide.cells.forEach((c, cellIdx) => {
            if (c.type === 'markdown') {
              // Strip heading on first markdown cell if it matches the slide title!
              const strip = cellIdx === 0;
              const mdHtml = this.formatMathAndMarkdown(c.source, strip);
              if (mdHtml) bodyHtml += `<div style="margin-bottom:0.6rem;">${mdHtml}</div>`;
            } else if (c.type === 'code') {
              if (config.showCode !== false) {
                bodyHtml += `
                  <div class="sheet-code-block" style="margin-bottom:0.5rem;">
                    ${c.source.replace(/</g, '&lt;').replace(/>/g, '&gt;')}
                  </div>
                `;
              }
              c.outputs.forEach(out => {
                if (out.hasImage && out.images.length) {
                  out.images.forEach(img => {
                    bodyHtml += `<div class="sheet-img-wrap" style="max-height:220px; text-align:center; margin:0.4rem 0;"><img src="${img}" style="max-height:200px; max-width:100%; object-fit:contain;" alt="Plot"></div>`;
                  });
                } else if (out.hasTable && out.html) {
                  bodyHtml += `<div style="overflow-x:auto; font-size:0.75rem; margin:0.4rem 0;">${out.html}</div>`;
                }
              });
            }
          });

          sheet.htmlContent = `
            <div style="flex:1; display:flex; flex-direction:column; justify-content:space-between; height:100%;">
              <div class="handout-slide-hdr" style="border-bottom:1.5px solid #171717; padding-bottom:0.5rem; margin-bottom:1rem;">
                <span class="handout-slide-title" style="font-size:1.35rem; font-family:var(--font-serif-display);">${slide.title}</span>
                <span class="handout-slide-badge" style="background:#171717; color:#ffffff; padding:0.2rem 0.6rem; border-radius:3px;">Slide ${idx + 1} / ${slidesList.length}</span>
              </div>
              <div style="flex:1; overflow:hidden;">
                ${bodyHtml || '<p class="sheet-prose" style="color:#827e77; font-style:italic;">(Diapositiva de transición)</p>'}
              </div>
            </div>
          `;
          sheets.push(sheet);
        });

      } else if (layout === 'handout') {
        // --- Mode 3: Handout (Slide-Printer study notes) ---
        const slidesList = this.buildSlidesList(nb);
        const notePatternClass = 'swatch-' + noteStyle;

        if (handoutLayout === '2-up') {
          // 2 slides per sheet
          for (let i = 0; i < slidesList.length; i += 2) {
            const sheet = createSheet(Math.floor(i / 2) + 1, Math.ceil(slidesList.length / 2));
            const s1 = slidesList[i];
            const s2 = slidesList[i + 1];

            const renderSlideContent = (s, num) => {
              let inner = '';
              s.cells.forEach((c, cIdx) => {
                if (c.type === 'markdown') {
                  inner += this.formatMathAndMarkdown(c.source, cIdx === 0);
                } else if (c.type === 'code') {
                  inner += `<div class="sheet-code-block" style="font-size:0.65rem; padding:3px 6px;">${c.source.slice(0, 150).replace(/</g, '&lt;').replace(/>/g, '&gt;')}</div>`;
                }
              });
              return `
                <div style="flex:1; display:flex; flex-direction:column;">
                  <div class="handout-slide-box">
                    <div class="handout-slide-hdr">
                      <span class="handout-slide-title">${s.title}</span>
                      <span class="handout-slide-badge">Slide ${num}</span>
                    </div>
                    <div style="font-size:0.8rem; max-height:85px; overflow:hidden;">
                      ${inner}
                    </div>
                  </div>
                  <div class="handout-notes-area ${notePatternClass}" style="min-height:140px; margin-top:0.6rem;"></div>
                </div>
              `;
            };

            sheet.htmlContent = `
              <div style="display:flex; flex-direction:column; gap:1.25rem; height:100%;">
                ${renderSlideContent(s1, i + 1)}
                ${s2 ? `<div style="border-top:1px dashed #d5cfc2; padding-top:0.75rem;">${renderSlideContent(s2, i + 2)}</div>` : ''}
              </div>
            `;
            sheets.push(sheet);
          }
        } else {
          // 1-up Standard
          slidesList.forEach((slide, idx) => {
            const sheet = createSheet(idx + 1, slidesList.length);
            sheet.footerText = `Diapositiva ${idx + 1} de ${slidesList.length}`;

            let slideBody = '';
            slide.cells.forEach((c, cIdx) => {
              if (c.type === 'markdown') {
                slideBody += this.formatMathAndMarkdown(c.source, cIdx === 0);
              } else if (c.type === 'code') {
                slideBody += `<div class="sheet-code-block" style="margin:0.4rem 0;">${c.source.slice(0, 200).replace(/</g, '&lt;').replace(/>/g, '&gt;')}</div>`;
              }
            });

            sheet.htmlContent = `
              <div style="display:flex; flex-direction:column; height:100%;">
                <div class="handout-slide-box">
                  <div class="handout-slide-hdr">
                    <span class="handout-slide-title">${slide.title}</span>
                    <span class="handout-slide-badge">Slide ${idx + 1}</span>
                  </div>
                  <div style="font-size:0.85rem; max-height:220px; overflow:hidden;">
                    ${slideBody}
                  </div>
                </div>

                <!-- Dedicated Note-Taking Area -->
                <div class="handout-notes-area ${notePatternClass}" style="flex:1; min-height:300px; margin-top:1rem;"></div>
              </div>
            `;
            sheets.push(sheet);
          });
        }

      } else if (layout === 'cheatsheet') {
        // --- Mode 4: Cheatsheet (Dense 2-Column Summary) ---
        const sheet = createSheet(1, 1);
        sheet.footerText = `${nb.title} · Cheatsheet Summary`;
        let col1 = '';
        let col2 = '';

        nb.cells.forEach((c, idx) => {
          let chunk = '';
          if (c.type === 'markdown') {
            chunk = `<div style="font-size:0.75rem; margin-bottom:0.75rem;">${this.formatMathAndMarkdown(c.source, false)}</div>`;
          } else if (c.type === 'code') {
            chunk = `
              <div class="sheet-code-block" style="font-size:0.65rem; padding:4px 6px; margin-bottom:0.5rem;">
                ${c.source.replace(/</g, '&lt;').replace(/>/g, '&gt;').slice(0, 200)}
              </div>
            `;
          }

          if (idx % 2 === 0) {
            col1 += chunk;
          } else {
            col2 += chunk;
          }
        });

        sheet.htmlContent = `
          <div style="font-family:var(--font-serif-display); font-size:1.4rem; font-weight:bold; border-bottom:1.5px solid #171717; padding-bottom:0.35rem; margin-bottom:0.75rem;">
            ${config.titleOverride || nb.title}
          </div>
          <div class="cheatsheet-cols">
            <div>${col1}</div>
            <div>${col2}</div>
          </div>
        `;
        sheets.push(sheet);
      }

      // Final pass to sync total sheet count across all footers
      const finalCount = sheets.length;
      sheets.forEach(s => {
        s.totalCount = finalCount;
        if (layout === 'slides') {
          s.footerText = `Slide ${s.pageNumber} / ${finalCount}`;
        } else {
          s.footerText = `Pág. ${s.pageNumber} de ${finalCount}`;
        }
      });

      return sheets;
    },

    /**
     * Builds authentic Typst markup matching nbpress templates.
     */
    generateTypst: function (nb, config) {
      config = config || {};
      const layout = config.layout || 'document';
      const theme = config.theme || 'editorial';
      const paper = config.paper === 'us-letter' ? 'us-letter' : (config.paper === 'a5' ? 'a5' : 'a4');
      const title = config.titleOverride || nb.title;

      let typst = `// ==========================================================================\n`;
      typst += `// Generated by nbpress · Editorial Jupyter Typesetting Engine\n`;
      typst += `// Layout: ${layout} | Theme: ${theme} | Paper: ${paper}\n`;
      typst += `// ==========================================================================\n\n`;

      typst += `#set page(\n`;
      typst += `  paper: "${paper}",\n`;
      typst += `  margin: (top: 2.2cm, bottom: 2.2cm, inside: 2.2cm, outside: 2.0cm),\n`;
      typst += `  header: context [\n`;
      typst += `    #text(size: 8pt, fill: luma(120))[\n`;
      typst += `      #grid(columns: (1fr, 1fr), align(left)[_${title}_], align(right)[nbpress ${theme}])\n`;
      typst += `      #line(length: 100%, stroke: 0.4pt + luma(200))\n`;
      typst += `    ]\n`;
      typst += `  ],\n`;
      typst += `  footer: context [\n`;
      typst += `    #align(center, text(size: 8.5pt, fill: luma(120))[\n`;
      typst += `      Pág. #counter(page).display("1") de #counter(page).final().first()\n`;
      typst += `    ])\n`;
      typst += `  ]\n`;
      typst += `)\n\n`;

      typst += `#set text(\n`;
      typst += `  font: ("Linux Libertine", "Times New Roman", "DejaVu Serif"),\n`;
      typst += `  size: 10pt,\n`;
      typst += `  lang: "es",\n`;
      typst += `)\n\n`;

      if (layout === 'document') {
        typst += `// Document Title\n`;
        typst += `#align(center)[\n`;
        typst += `  #text(size: 22pt, weight: "bold")[${title}]\n`;
        if (nb.authors.length) {
          typst += `  #v(8pt)\n  #text(size: 11pt, fill: luma(80))[${nb.authors.join(', ')}]\n`;
        }
        typst += `]\n#v(16pt)\n\n`;
      }

      nb.cells.forEach((cell, idx) => {
        typst += `// Cell ${idx + 1} (${cell.type})\n`;
        if (cell.type === 'markdown') {
          typst += `${cell.source}\n\n`;
        } else if (cell.type === 'code' && config.showCode !== false) {
          typst += `\`\`\`${nb.language}\n${cell.source}\n\`\`\`\n\n`;
        }
      });

      return typst;
    },

    buildCliCommand: function (nb, config) {
      let cmd = `nbpress build "${nb.fileName}"`;
      if (config.layout && config.layout !== 'document') {
        cmd += ` --layout ${config.layout}`;
      }
      if (config.theme && config.theme !== 'editorial') {
        cmd += ` --theme ${config.theme}`;
      }
      if (config.paper && config.paper !== 'a4') {
        cmd += ` --paper ${config.paper}`;
      }
      if (config.eco) {
        cmd += ` --eco`;
      }
      if (config.gutter && config.gutter !== 'none') {
        cmd += config.gutter === 'spiral' ? ' --spiral' : ' --gutter 1.5cm';
      }
      if (config.layout === 'handout') {
        if (config.handoutNoteStyle && config.handoutNoteStyle !== 'lines') {
          cmd += ` --handout-style ${config.handoutNoteStyle}`;
        }
        if (config.handoutLayout === '2-up') {
          cmd += ` --handout-layout 2-up`;
        }
      }
      return cmd;
    }
  };

  window.NbpressEngine = NbpressEngine;
})(window);
