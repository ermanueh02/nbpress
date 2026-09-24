/**
 * nbpress Preview Controller · Multi-Page Sheet Navigator, Zoom Engine & Multi-Page Print Pipeline
 */

(function (window) {
  'use strict';

  function NbpressPreview(options) {
    this.container = options.container;
    this.printContainer = document.getElementById('printContainer');
    this.sheets = [];
    this.currentIndex = 0;
    this.zoomLevel = 1.0;
    this.onPageChange = options.onPageChange || function () {};

    this.initKeyboard();
  }

  NbpressPreview.prototype.initKeyboard = function () {
    const self = this;
    window.addEventListener('keydown', function (e) {
      if (['INPUT', 'TEXTAREA', 'SELECT'].includes(e.target.tagName)) return;

      if (e.key === 'ArrowRight' || e.key === 'PageDown') {
        self.next();
      } else if (e.key === 'ArrowLeft' || e.key === 'PageUp') {
        self.prev();
      }
    });
  };

  NbpressPreview.prototype.setSheets = function (sheets) {
    this.sheets = sheets || [];
    this.currentIndex = 0;
    this.render();
    this.renderPrintContainer();
  };

  /**
   * Renders the single active sheet into the interactive screen viewport.
   */
  NbpressPreview.prototype.render = function () {
    if (!this.container) return;

    if (!this.sheets.length) {
      this.container.innerHTML = `
        <div style="text-align:center; padding:4rem 1rem; color:var(--text-muted);">
          <p style="font-size:1.1rem; font-weight:600;">No hay hojas disponibles para previsualizar</p>
          <p style="font-size:0.85rem;">Carga un cuaderno Jupyter (.ipynb) para generar la maqueta editorial.</p>
        </div>
      `;
      return;
    }

    const currentSheet = this.sheets[this.currentIndex] || this.sheets[0];

    // Set body layout attribute for print orientation styling
    document.body.setAttribute('data-layout', currentSheet.isSlide ? 'slides' : 'document');

    let holeGuidesHtml = '';
    if (currentSheet.holeGuides) {
      holeGuidesHtml = `
        <div class="hole-guide" style="top: 25%;"></div>
        <div class="hole-guide" style="top: 75%;"></div>
      `;
    }

    const slideClass = currentSheet.isSlide ? 'sheet-slides' : '';

    const html = `
      <div class="paper-sheet ${slideClass} ${currentSheet.gutterClass || ''}" style="transform: scale(${this.zoomLevel}); transform-origin: top center;">
        ${holeGuidesHtml}
        
        <!-- Sheet Running Header -->
        <div class="sheet-header">
          <span>${currentSheet.headerText}</span>
          <span>nbpress</span>
        </div>

        <!-- Sheet Body Content -->
        <div class="sheet-body">
          ${currentSheet.htmlContent}
        </div>

        <!-- Sheet Running Footer -->
        <div class="sheet-footer">
          ${currentSheet.footerText}
        </div>
      </div>
    `;

    this.container.innerHTML = html;
    this.onPageChange(this.currentIndex + 1, this.sheets.length);
  };

  /**
   * Renders ALL sheets into the print container so window.print() prints every page!
   */
  NbpressPreview.prototype.renderPrintContainer = function () {
    const printContainer = this.printContainer || document.getElementById('printContainer');
    if (!printContainer) return;

    if (!this.sheets.length) {
      printContainer.innerHTML = '';
      return;
    }

    let allHtml = '';
    this.sheets.forEach(sheet => {
      let holeGuidesHtml = '';
      if (sheet.holeGuides) {
        holeGuidesHtml = `
          <div class="hole-guide" style="top: 25%;"></div>
          <div class="hole-guide" style="top: 75%;"></div>
        `;
      }

      const slideClass = sheet.isSlide ? 'sheet-slides' : '';

      allHtml += `
        <div class="paper-sheet print-sheet ${slideClass} ${sheet.gutterClass || ''}">
          ${holeGuidesHtml}
          <div class="sheet-header">
            <span>${sheet.headerText}</span>
            <span>nbpress</span>
          </div>
          <div class="sheet-body">
            ${sheet.htmlContent}
          </div>
          <div class="sheet-footer">
            ${sheet.footerText}
          </div>
        </div>
      `;
    });

    printContainer.innerHTML = allHtml;
  };

  NbpressPreview.prototype.printAll = function () {
    this.renderPrintContainer();
    window.print();
  };

  NbpressPreview.prototype.next = function () {
    if (this.currentIndex < this.sheets.length - 1) {
      this.currentIndex++;
      this.render();
    }
  };

  NbpressPreview.prototype.prev = function () {
    if (this.currentIndex > 0) {
      this.currentIndex--;
      this.render();
    }
  };

  NbpressPreview.prototype.goTo = function (index) {
    if (index >= 0 && index < this.sheets.length) {
      this.currentIndex = index;
      this.render();
    }
  };

  NbpressPreview.prototype.zoomIn = function () {
    if (this.zoomLevel < 1.6) {
      this.zoomLevel += 0.1;
      this.render();
    }
  };

  NbpressPreview.prototype.zoomOut = function () {
    if (this.zoomLevel > 0.6) {
      this.zoomLevel -= 0.1;
      this.render();
    }
  };

  NbpressPreview.prototype.resetZoom = function () {
    this.zoomLevel = 1.0;
    this.render();
  };

  window.NbpressPreview = NbpressPreview;
})(window);
