/**
 * nbpress Preview Controller · Multi-Page Sheet Navigator & Zoom Engine
 */

(function (window) {
  'use strict';

  function NbpressPreview(options) {
    this.container = options.container;
    this.sheets = [];
    this.currentIndex = 0;
    this.zoomLevel = 1.0;
    this.onPageChange = options.onPageChange || function () {};

    this.initKeyboard();
  }

  NbpressPreview.prototype.initKeyboard = function () {
    const self = this;
    window.addEventListener('keydown', function (e) {
      // Only when preview is visible and not typing in an input
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
  };

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

    // Build hole guide elements if enabled
    let holeGuidesHtml = '';
    if (currentSheet.holeGuides) {
      // ISO 838 standard hole punch positions
      holeGuidesHtml = `
        <div class="hole-guide" style="top: 25%;"></div>
        <div class="hole-guide" style="top: 75%;"></div>
      `;
    }

    const html = `
      <div class="paper-sheet ${currentSheet.gutterClass || ''}" style="transform: scale(${this.zoomLevel}); transform-origin: top center;">
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
