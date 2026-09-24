/**
 * nbpress Engine · In-Browser Notebook Parser & Typst Markup Generator
 * 100% Client-Side · Private · Instantaneous
 */

(function (window) {
  'use strict';

  const NbpressEngine = {
    /**
     * Parses .ipynb JSON file content into a structured notebook document.
     * @param {string|object} input - Raw JSON text or parsed object
     * @param {string} fileName - Optional file name
     * @returns {object} Structured notebook document
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
          if (firstLine.startsWith('# ') || firstLine.startsWith('## ')) {
            cell.isSlideStarter = true;
          }
        }

        if (cell.isSlideStarter) {
          currentSlideIndex++;
          nb.stats.slidesCount++;
          // Extract heading title
          const match = cell.source.match(/^#{1,3}\s+(.+)$/m);
          cell.slideTitle = match ? match[1].trim() : `Slide ${currentSlideIndex}`;
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

    /**
     * Attempts to find an editorial title for the document.
     */
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
     * Converts raw LaTeX / Markdown math blocks to clean styled HTML.
     */
    formatMathAndMarkdown: function (text) {
      if (!text) return '';

      // Escape HTML basic
      let safe = text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');

      // Block math $$ ... $$
      safe = safe.replace(/\$\$([\s\S]*?)\$\$/g, function (m, eq) {
        return `<div class="sheet-math-box">$$ ${eq.trim()} $$</div>`;
      });

      // Inline math $ ... $
      safe = safe.replace(/\$([^\$\n]+?)\$/g, function (m, eq) {
        return `<span style="font-family:'Newsreader',Georgia,serif; font-style:italic;">$${eq}$</span>`;
      });

      // Headers
      safe = safe.replace(/^# (.*$)/gim, '<h1 class="sheet-title">$1</h1>');
      safe = safe.replace(/^## (.*$)/gim, '<h2 style="font-family:var(--font-serif-display); font-size:1.3rem; margin-top:0.8rem; margin-bottom:0.4rem; color:#171717;">$1</h2>');
      safe = safe.replace(/^### (.*$)/gim, '<h3 style="font-size:1rem; font-weight:700; margin-top:0.6rem; color:#171717;">$1</h3>');

      // Blockquotes
      safe = safe.replace(/^\> (.*$)/gim, '<blockquote style="border-left:3px solid #c2410c; padding-left:0.8rem; margin:0.6rem 0; color:#52504b; font-style:italic;">$1</blockquote>');

      // Bold & Italic
      safe = safe.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
      safe = safe.replace(/\*(.*?)\*/g, '<em>$1</em>');
      safe = safe.replace(/`([^`]+)`/g, '<code style="background:#f0ece3; padding:1px 4px; border-radius:3px; font-family:var(--font-mono); font-size:0.8em;">$1</code>');

      // Markdown Tables
      safe = safe.replace(/(\|.+?\|\n)+/g, function (match) {
        const lines = match.trim().split('\n');
        if (lines.length < 2) return match;
        let html = '<table style="width:100%; border-collapse:collapse; margin:0.6rem 0; font-size:0.75rem;">';
        lines.forEach((line, idx) => {
          if (idx === 1 && line.includes('---')) return; // separator
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
        html += '</table>';
        return html;
      });

      // Paragraphs
      return safe.split('\n\n').map(p => {
        if (p.startsWith('<h') || p.startsWith('<div') || p.startsWith('<block') || p.startsWith('<table')) {
          return p;
        }
        return `<p class="sheet-prose">${p.replace(/\n/g, '<br>')}</p>`;
      }).join('');
    },

    /**
     * Generates simulated print pages for the preview canvas & browser print engine.
     * @param {object} nb - Parsed notebook document
     * @param {object} config - Configuration object
     * @returns {Array<object>} List of rendered sheets
     */
    generateSheets: function (nb, config) {
      config = config || {};
      const layout = config.layout || 'document';
      const theme = config.theme || 'editorial';
      const paper = config.paper || 'a4';
      const gutter = config.gutter || 'none';
      const duplex = !!config.duplex;
      const holeGuides = !!config.holeGuides;
      const eco = !!config.eco;
      const noteStyle = config.handoutNoteStyle || 'lines';
      const handoutLayout = config.handoutLayout || '1-up';

      const sheets = [];

      // Helper to create sheet skeleton
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
          headerText: `${nb.title} · nbpress ${theme}`,
          footerText: `Pág. ${sheetNum} de ${totalSheets}`,
          htmlContent: ''
        };
      };

      if (layout === 'document') {
        // Mode 1: Document (Cover + Continuous Sections)
        let totalEstSheets = Math.max(2, Math.ceil(nb.cells.length / 5) + 1);

        // Sheet 1: Editorial Cover Page
        if (config.cover !== false) {
          const coverSheet = createSheet(1, totalEstSheets);
          coverSheet.htmlContent = `
            <div style="flex:1; display:flex; flex-direction:column; justify-content:center; align-items:flex-start; padding:2rem 0;">
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

        // Subsequent Content Sheets
        let currentSheet = createSheet(sheets.length + 1, totalEstSheets);
        let itemsInSheet = 0;

        nb.cells.forEach(cell => {
          if (itemsInSheet >= 4) {
            sheets.push(currentSheet);
            currentSheet = createSheet(sheets.length + 1, totalEstSheets);
            itemsInSheet = 0;
          }

          if (cell.type === 'markdown') {
            currentSheet.htmlContent += `<div style="margin-bottom:1rem;">${this.formatMathAndMarkdown(cell.source)}</div>`;
            itemsInSheet++;
          } else if (cell.type === 'code' && config.showCode !== false) {
            const prompt = config.showPrompts !== false ? `<span class="sheet-code-prompt">In [${cell.executionCount || ' '}]:</span> ` : '';
            currentSheet.htmlContent += `
              <div class="sheet-code-block" style="${eco ? 'background:#ffffff; border-color:#d5cfc2;' : ''}">
                ${prompt}${cell.source.replace(/</g, '&lt;').replace(/>/g, '&gt;')}
              </div>
            `;
            itemsInSheet++;

            // Outputs
            cell.outputs.forEach(out => {
              if (out.hasImage && out.images.length) {
                out.images.forEach(imgSrc => {
                  currentSheet.htmlContent += `
                    <div class="sheet-img-wrap" style="margin:0.5rem 0;">
                      <img src="${imgSrc}" alt="Rendered Plot">
                    </div>
                  `;
                  itemsInSheet += 2;
                });
              } else if (out.hasTable && out.html) {
                currentSheet.htmlContent += `<div style="overflow-x:auto; margin:0.5rem 0;">${out.html}</div>`;
                itemsInSheet++;
              } else if (out.text && !out.isError) {
                currentSheet.htmlContent += `
                  <div style="font-family:var(--font-mono); font-size:0.68rem; color:#52504b; background:#fcfbf9; padding:4px 8px; border-left:2px solid #a39f97; margin:0.35rem 0; white-space:pre-wrap;">
                    ${out.text.replace(/</g, '&lt;').replace(/>/g, '&gt;').slice(0, 400)}
                  </div>
                `;
              }
            });
          }
        });

        if (currentSheet.htmlContent) {
          sheets.push(currentSheet);
        }

      } else if (layout === 'slides') {
        // Mode 2: Slides (16:9 Landscape Presentations)
        let slideCells = nb.cells.filter(c => c.isSlideStarter);
        if (!slideCells.length) slideCells = nb.cells.slice(0, 10);

        slideCells.forEach((c, idx) => {
          const sheet = createSheet(idx + 1, slideCells.length);
          sheet.footerText = `Diapositiva ${idx + 1} de ${slideCells.length}`;
          sheet.htmlContent = `
            <div style="flex:1; display:flex; flex-direction:column; justify-content:space-between;">
              <div class="handout-slide-hdr">
                <span class="handout-slide-title">${c.slideTitle || `Sección ${idx + 1}`}</span>
                <span class="handout-slide-badge">Slide ${idx + 1} / ${slideCells.length}</span>
              </div>
              <div style="flex:1; padding:1.25rem 0;">
                ${this.formatMathAndMarkdown(c.source)}
              </div>
              <div style="border-top:1px solid #e2ddd3; padding-top:0.5rem; display:flex; justify-content:space-between; font-size:0.7rem; color:#827e77;">
                <span>${nb.title}</span>
                <span>nbpress slides · 16:9</span>
              </div>
            </div>
          `;
          sheets.push(sheet);
        });

      } else if (layout === 'handout') {
        // Mode 3: Handout (Slide-Printer study notes)
        let slideCells = nb.cells.filter(c => c.isSlideStarter);
        if (!slideCells.length) slideCells = nb.cells.slice(0, 8);

        let notePatternClass = 'swatch-' + noteStyle;

        if (handoutLayout === '2-up') {
          // 2 slides per sheet
          for (let i = 0; i < slideCells.length; i += 2) {
            const sheet = createSheet(Math.floor(i / 2) + 1, Math.ceil(slideCells.length / 2));
            const c1 = slideCells[i];
            const c2 = slideCells[i + 1];

            sheet.htmlContent = `
              <div style="display:flex; flex-direction:column; gap:1.25rem; height:100%;">
                <!-- Slide 1 -->
                <div style="flex:1; display:flex; flex-direction:column;">
                  <div class="handout-slide-box">
                    <div class="handout-slide-hdr">
                      <span class="handout-slide-title">${c1.slideTitle}</span>
                      <span class="handout-slide-badge">Slide ${i + 1}</span>
                    </div>
                    <div style="font-size:0.8rem; max-height:80px; overflow:hidden;">
                      ${this.formatMathAndMarkdown(c1.source).slice(0, 200)}...
                    </div>
                  </div>
                  <div class="handout-notes-area ${notePatternClass}" style="min-height:140px;"></div>
                </div>

                ${c2 ? `
                <!-- Slide 2 -->
                <div style="flex:1; display:flex; flex-direction:column; border-top:1px dashed #d5cfc2; padding-top:1rem;">
                  <div class="handout-slide-box">
                    <div class="handout-slide-hdr">
                      <span class="handout-slide-title">${c2.slideTitle}</span>
                      <span class="handout-slide-badge">Slide ${i + 2}</span>
                    </div>
                    <div style="font-size:0.8rem; max-height:80px; overflow:hidden;">
                      ${this.formatMathAndMarkdown(c2.source).slice(0, 200)}...
                    </div>
                  </div>
                  <div class="handout-notes-area ${notePatternClass}" style="min-height:140px;"></div>
                </div>
                ` : ''}
              </div>
            `;
            sheets.push(sheet);
          }
        } else {
          // 1-up Standard
          slideCells.forEach((c, idx) => {
            const sheet = createSheet(idx + 1, slideCells.length);
            sheet.footerText = `Diapositiva ${idx + 1} de ${slideCells.length}`;
            sheet.htmlContent = `
              <div style="display:flex; flex-direction:column; height:100%;">
                <div class="handout-slide-box">
                  <div class="handout-slide-hdr">
                    <span class="handout-slide-title">${c.slideTitle}</span>
                    <span class="handout-slide-badge">Slide ${idx + 1}</span>
                  </div>
                  <div style="font-size:0.85rem; max-height:180px; overflow:hidden;">
                    ${this.formatMathAndMarkdown(c.source)}
                  </div>
                </div>

                <!-- Note-Taking Area -->
                <div class="handout-notes-area ${notePatternClass}"></div>
              </div>
            `;
            sheets.push(sheet);
          });
        }

      } else if (layout === 'cheatsheet') {
        // Mode 4: Cheatsheet (Dense 2-Column Summary)
        const sheet = createSheet(1, 1);
        sheet.footerText = `${nb.title} · Cheatsheet Summary`;
        let col1 = '';
        let col2 = '';

        nb.cells.forEach((c, idx) => {
          let chunk = '';
          if (c.type === 'markdown') {
            chunk = `<div style="font-size:0.75rem; margin-bottom:0.75rem;">${this.formatMathAndMarkdown(c.source)}</div>`;
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

      // Update total sheet counters
      const finalCount = sheets.length;
      sheets.forEach(s => {
        s.totalCount = finalCount;
        s.footerText = `Pág. ${s.pageNumber} de ${finalCount}`;
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
      const eco = !!config.eco;
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

    /**
     * Builds the exact CLI command line to reproduce current configuration.
     */
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
