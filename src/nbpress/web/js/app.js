/**
 * nbpress Studio · Main Application Logic & Interactive State Controller
 * Multilingual (EN/ES/GL), PWA, Drag-and-Drop, Typst Generator & Direct Browser Print Engine.
 */

(function () {
  'use strict';

  // --- Multilingual Translations Dictionary ---
  const I18N = {
    en: {
      brandSubtitle: 'Editorial Jupyter Typesetting',
      privacyBadge: '100% Private · In-Browser',
      themeSystem: 'System',
      themeLight: 'Light',
      themeDark: 'Dark',
      installBtn: 'Install App',
      heroSuper: 'Jupyter to Editorial PDF Studio',
      heroTitle: 'Transform Notebooks into Print-Ready Editorial Documents',
      heroSubtitle: 'Publish academic reports, 16:9 presentation slides, Slide-Printer study handouts with note-taking space, and compact 2-column revision sheets directly in your browser or from the command line.',
      dropTitle: 'Drop your Jupyter Notebook (.ipynb) here',
      dropDesc: 'or select from your local files to preview and compile instantly',
      dropBtn: 'Choose .ipynb File',
      sampleLabel: 'Or explore with samples:',
      sampleAnalysis: 'Quantitative Analysis & ML',
      sampleSlides: 'Lecture Slides Deck',
      feat1Num: '01',
      feat1Title: 'Typst Editorial Typography',
      feat1Desc: 'Publication-grade typography, mathematical formula rendering, crisp table borders, and automatic page numbers.',
      feat2Num: '02',
      feat2Title: '4 Purpose-Built Layouts',
      feat2Desc: 'Academic continuous report, widescreen slides, Slide-Printer handwritten handouts, and dense 2-column cheatsheets.',
      feat3Num: '03',
      feat3Title: '100% Private & In-Browser',
      feat3Desc: 'Everything is processed locally in your browser memory. Zero files are uploaded to any remote server.',
      sectionLayout: 'Layout Architecture',
      layoutDocTitle: 'Document',
      layoutDocDesc: 'Academic report with cover, TOC & running headers',
      layoutSlidesTitle: 'Slides',
      layoutSlidesDesc: '16:9 widescreen presentation deck with category badges',
      layoutHandoutTitle: 'Handout',
      layoutHandoutDesc: 'Slide-Printer: top slide + bottom note-taking area',
      layoutCheatTitle: 'Cheatsheet',
      layoutCheatDesc: 'Dense 2-column revision sheet to save paper',
      sectionTheme: 'Visual Theme',
      themeEditorialTitle: 'Editorial',
      themeMcmTitle: 'Mid-Century',
      themeMinimalTitle: 'Minimal',
      sectionGeometry: 'Print Geometry & Paper',
      paperLabel: 'Paper Size',
      gutterLabel: 'Binding Margin',
      gutterNone: 'None',
      gutterBinder: 'Binder (+11mm)',
      gutterSpiral: 'Spiral (+8mm)',
      duplexTitle: 'Duplex Printing',
      duplexSub: 'Alternates binding margin between odd & even pages',
      holeTitle: 'Hole Punch Guides',
      holeSub: 'Subtle ISO 838 crosshairs on edge',
      sectionNotes: 'Handout Note Style',
      noteLinesTitle: 'Ruled Lines',
      noteGridTitle: 'Graph Grid',
      noteDotsTitle: 'Bullet Dots',
      noteBlankTitle: 'Blank Space',
      sectionEco: 'Ink & Code Options',
      ecoTitle: 'Eco / Ink-Saver Mode',
      ecoSub: 'Light syntax highlighting to save printer toner',
      showCodeTitle: 'Show Code Cells',
      showPromptsTitle: 'Show In [x] Labels',
      sectionCli: 'CLI Command Line',
      tabPreview: 'Sheet Preview',
      tabOutline: 'Cell Outline',
      tabTypst: 'Typst Source',
      printBtn: 'Print / Save PDF',
      downloadTypstBtn: 'Download .typ',
      copyCliBtn: 'Copy Command',
      changeFileBtn: 'Change Notebook',
      addFilesBtn: '+ Add Another',
      batchDownload: 'Download Batch (ZIP)'
    },
    es: {
      brandSubtitle: 'Maquetación Editorial de Jupyter',
      privacyBadge: '100% Privado · En el Navegador',
      themeSystem: 'Sistema',
      themeLight: 'Claro',
      themeDark: 'Oscuro',
      installBtn: 'Instalar App',
      heroSuper: 'Estudio Jupyter a PDF Editorial',
      heroTitle: 'Transforma tus Notebooks en Documentos Editoriales de Imprenta',
      heroSubtitle: 'Publica informes académicos, diapositivas 16:9, apuntes de estudio Slide-Printer con pauta manuscrita y esquemas compactos a 2 columnas directamente en tu navegador o desde el terminal.',
      dropTitle: 'Arrastra tu cuaderno Jupyter (.ipynb) aquí',
      dropDesc: 'o selecciona de tus archivos locales para previsualizar y compilar al instante',
      dropBtn: 'Elegir archivo .ipynb',
      sampleLabel: 'O prueba con ejemplos:',
      sampleAnalysis: 'Análisis Cuantitativo y ML',
      sampleSlides: 'Diapositivas de Clase',
      feat1Num: '01',
      feat1Title: 'Tipografía Editorial Typst',
      feat1Desc: 'Calidad de publicación con fórmulas matemáticas, tablas nítidas, ligaduras tipográficas y paginación automática.',
      feat2Num: '02',
      feat2Title: '4 Maquetaciones Especializadas',
      feat2Desc: 'Informe continuo con portada, slides panorámicas, apuntes Slide-Printer con pauta y hojas de repaso a 2 columnas.',
      feat3Num: '03',
      feat3Title: '100% Privado en tu Navegador',
      feat3Desc: 'Todo se procesa localmente en la memoria de tu navegador. Ningún dato ni archivo sale jamás de tu equipo.',
      sectionLayout: 'Arquitectura de Maquetación',
      layoutDocTitle: 'Documento',
      layoutDocDesc: 'Informe académico con portada, índice y encabezados',
      layoutSlidesTitle: 'Diapositivas',
      layoutSlidesDesc: 'Presentación 16:9 moderna con distintivos por sección',
      layoutHandoutTitle: 'Handout (Apuntes)',
      layoutHandoutDesc: 'Slide-Printer: diapositiva arriba + área de notas abajo',
      layoutCheatTitle: 'Cheatsheet',
      layoutCheatDesc: 'Esquema a 2 columnas compacto para ahorrar papel',
      sectionTheme: 'Tema Visual',
      themeEditorialTitle: 'Editorial',
      themeMcmTitle: 'Mid-Century',
      themeMinimalTitle: 'Minimalista',
      sectionGeometry: 'Geometría de Impresión y Papel',
      paperLabel: 'Tamaño de Papel',
      gutterLabel: 'Margen de Encuadernación',
      gutterNone: 'Ninguno',
      gutterBinder: 'Carpetas (+11mm)',
      gutterSpiral: 'Espiral (+8mm)',
      duplexTitle: 'Impresión a Doble Cara (Dúplex)',
      duplexSub: 'Alterna el margen de lomo entre páginas pares e impares',
      holeTitle: 'Marcas de Perforación',
      holeSub: 'Guías de taladro sutiles ISO 838 en el lomo',
      sectionNotes: 'Estilo de Notas Handout',
      noteLinesTitle: 'Líneas Pautadas',
      noteGridTitle: 'Cuadrícula',
      noteDotsTitle: 'Puntos Bullet',
      noteBlankTitle: 'Espacio Blanco',
      sectionEco: 'Opciones de Tinta y Código',
      ecoTitle: 'Modo Eco / Ahorro de Tinta',
      ecoSub: 'Fondos claros y alto contraste para ahorrar tóner',
      showCodeTitle: 'Mostrar Celdas de Código',
      showPromptsTitle: 'Mostrar Etiquetas In [x]',
      sectionCli: 'Comando de Terminal (CLI)',
      tabPreview: 'Vista Previa Hojas',
      tabOutline: 'Estructura Celdas',
      tabTypst: 'Código Typst',
      printBtn: 'Imprimir / Guardar PDF',
      downloadTypstBtn: 'Descargar .typ',
      copyCliBtn: 'Copiar Comando',
      changeFileBtn: 'Cambiar Cuaderno',
      addFilesBtn: '+ Añadir Otro',
      batchDownload: 'Descargar Lote (ZIP)'
    },
    gl: {
      brandSubtitle: 'Maquetación Editorial de Jupyter',
      privacyBadge: '100% Privado · No Navegador',
      themeSystem: 'Sistema',
      themeLight: 'Claro',
      themeDark: 'Escuro',
      installBtn: 'Instalar App',
      heroSuper: 'Estudo Jupyter a PDF Editorial',
      heroTitle: 'Transforma os teus Cadernos en Documentos Editoriais de Imprenta',
      heroSubtitle: 'Publica informes académicos, diapositivas 16:9, follas de estudo Slide-Printer con pauta manuscrita e esquemas compactos a 2 columnas directamente no teu navegador.',
      dropTitle: 'Arrastra o teu caderno Jupyter (.ipynb) aquí',
      dropDesc: 'ou selecciona dos teus ficheiros locais para previsualizar e compilar ao instante',
      dropBtn: 'Elixir ficheiro .ipynb',
      sampleLabel: 'Ou proba con exemplos:',
      sampleAnalysis: 'Análise Cuantitativa e ML',
      sampleSlides: 'Diapositivas de Clase',
      feat1Num: '01',
      feat1Title: 'Tipografía Editorial Typst',
      feat1Desc: 'Calidade de publicación con fórmulas matemáticas, táboas nítidas, ligaduras e paxinado automático.',
      feat2Num: '02',
      feat2Title: '4 Maquetacións Especializadas',
      feat2Desc: 'Informe continuo con portada, slides panorámicas, apuntamentos con pauta e follas de repaso a 2 columnas.',
      feat3Num: '03',
      feat3Title: '100% Privado no teu Navegador',
      feat3Desc: 'Todo se procesa localmente na memoria do teu navegador. Ningún ficheiro se sube a ningún servidor.',
      sectionLayout: 'Arquitectura de Maquetación',
      layoutDocTitle: 'Documento',
      layoutDocDesc: 'Informe académico con portada, índice e cabeceiras',
      layoutSlidesTitle: 'Diapositivas',
      layoutSlidesDesc: 'Presentación 16:9 moderna con distintivos por sección',
      layoutHandoutTitle: 'Handout (Apuntes)',
      layoutHandoutDesc: 'Slide-Printer: diapositiva arriba + área de notas abaixo',
      layoutCheatTitle: 'Cheatsheet',
      layoutCheatDesc: 'Esquema a 2 columnas compacto para aforrar papel',
      sectionTheme: 'Tema Visual',
      themeEditorialTitle: 'Editorial',
      themeMcmTitle: 'Mid-Century',
      themeMinimalTitle: 'Minimalista',
      sectionGeometry: 'Xeometría de Impresión e Papel',
      paperLabel: 'Tamaño de Papel',
      gutterLabel: 'Marxe de Encuadernación',
      gutterNone: 'Ningún',
      gutterBinder: 'Carpetas (+11mm)',
      gutterSpiral: 'Espiral (+8mm)',
      duplexTitle: 'Impresión a Dobre Cara (Dúplex)',
      duplexSub: 'Alterna a marxe de lombo entre páxinas pares e impares',
      holeTitle: 'Marcas de Perforación',
      holeSub: 'Guías de trade sutiles ISO 838 no lombo',
      sectionNotes: 'Estilo de Notas Handout',
      noteLinesTitle: 'Liñas Pautadas',
      noteGridTitle: 'Cadriculado',
      noteDotsTitle: 'Puntos Bullet',
      noteBlankTitle: 'Espazo Branco',
      sectionEco: 'Opcións de Tinta e Código',
      ecoTitle: 'Modo Eco / Aforro de Tinta',
      ecoSub: 'Fondos claros e alto contraste para aforrar tóner',
      showCodeTitle: 'Amosar Celdas de Código',
      showPromptsTitle: 'Amosar Etiquetas In [x]',
      sectionCli: 'Comando de Terminal (CLI)',
      tabPreview: 'Vista Previa Follas',
      tabOutline: 'Estrutura Celdas',
      tabTypst: 'Código Typst',
      printBtn: 'Imprimir / Gardar PDF',
      downloadTypstBtn: 'Descargar .typ',
      copyCliBtn: 'Copiar Comando',
      changeFileBtn: 'Cambiar Caderno',
      addFilesBtn: '+ Engadir Outro',
      batchDownload: 'Descargar Lote (ZIP)'
    }
  };

  // --- App State ---
  const state = {
    lang: localStorage.getItem('nbpress_lang') || 'en',
    themeMode: localStorage.getItem('nbpress_theme_mode') || 'auto',
    activeNotebook: null,
    batchQueue: [],
    config: {
      layout: 'document',
      theme: 'editorial',
      paper: 'a4',
      gutter: 'none',
      duplex: false,
      holeGuides: false,
      eco: false,
      cover: true,
      showCode: true,
      showPrompts: true,
      handoutNoteStyle: 'lines',
      handoutLayout: '1-up',
      titleOverride: ''
    },
    activeTab: 'preview' // 'preview', 'outline', 'typst'
  };

  let previewController = null;
  let deferredPrompt = null;

  // --- DOM Elements ---
  const el = {
    initialHero: document.getElementById('initialHero'),
    workspace: document.getElementById('workspace'),
    dropzone: document.getElementById('dropzone'),
    fileInput: document.getElementById('fileInput'),
    metaFileName: document.getElementById('metaFileName'),
    metaCellCount: document.getElementById('metaCellCount'),
    metaCodeCount: document.getElementById('metaCodeCount'),
    metaImagesCount: document.getElementById('metaImagesCount'),
    metaTablesCount: document.getElementById('metaTablesCount'),
    metaSlidesCount: document.getElementById('metaSlidesCount'),
    cliSnippet: document.getElementById('cliSnippet'),
    copyCliBtn: document.getElementById('copyCliBtn'),
    previewViewport: document.getElementById('previewCanvasViewport'),
    pageCounterText: document.getElementById('pageCounterText'),
    prevPageBtn: document.getElementById('prevPageBtn'),
    nextPageBtn: document.getElementById('nextPageBtn'),
    zoomInBtn: document.getElementById('zoomInBtn'),
    zoomOutBtn: document.getElementById('zoomOutBtn'),
    resetZoomBtn: document.getElementById('resetZoomBtn'),
    tabPreviewBtn: document.getElementById('tabPreviewBtn'),
    tabOutlineBtn: document.getElementById('tabOutlineBtn'),
    tabTypstBtn: document.getElementById('tabTypstBtn'),
    outlineViewContainer: document.getElementById('outlineViewContainer'),
    typstViewContainer: document.getElementById('typstViewContainer'),
    typstSourceCode: document.getElementById('typstSourceCode'),
    handoutSettingsCard: document.getElementById('handoutSettingsCard'),
    printPdfBtn: document.getElementById('printPdfBtn'),
    downloadTypstBtn: document.getElementById('downloadTypstBtn'),
    replaceFileBtn: document.getElementById('replaceFileBtn'),
    addFilesHeaderBtn: document.getElementById('addFilesHeaderBtn'),
    batchBar: document.getElementById('batchBar'),
    batchCountBadge: document.getElementById('batchCountBadge'),
    batchTabsTrack: document.getElementById('batchTabsTrack'),
    exportBatchBtn: document.getElementById('exportBatchBtn'),
    installAppBtn: document.getElementById('installAppBtn'),
    themeToggleBtn: document.getElementById('themeToggleBtn')
  };

  // --- Initialization ---
  function init() {
    initTheme();
    initLanguage();
    initPWA();
    initEventListeners();

    previewController = new window.NbpressPreview({
      container: el.previewViewport,
      onPageChange: function (current, total) {
        if (el.pageCounterText) {
          el.pageCounterText.textContent = `${current} / ${total}`;
        }
        if (el.prevPageBtn) el.prevPageBtn.disabled = current <= 1;
        if (el.nextPageBtn) el.nextPageBtn.disabled = current >= total;
      }
    });
  }

  // --- Theme Management ---
  function initTheme() {
    applyTheme(state.themeMode);
  }

  function applyTheme(mode) {
    state.themeMode = mode;
    localStorage.setItem('nbpress_theme_mode', mode);

    const doc = document.documentElement;
    if (mode === 'light') {
      doc.setAttribute('data-theme', 'light');
    } else if (mode === 'dark') {
      doc.setAttribute('data-theme', 'dark');
    } else {
      doc.removeAttribute('data-theme');
    }
    updateThemeButtonText();
  }

  function updateThemeButtonText() {
    if (!el.themeToggleBtn) return;
    const txt = el.themeToggleBtn.querySelector('#themeModeText');
    const ico = el.themeToggleBtn.querySelector('#themeModeIcon');
    const strings = I18N[state.lang] || I18N.en;

    if (state.themeMode === 'light') {
      if (txt) txt.textContent = strings.themeLight;
      if (ico) ico.textContent = '☀';
    } else if (state.themeMode === 'dark') {
      if (txt) txt.textContent = strings.themeDark;
      if (ico) ico.textContent = '🌙';
    } else {
      if (txt) txt.textContent = strings.themeSystem;
      if (ico) ico.textContent = '◐';
    }
  }

  // --- Language Management ---
  function initLanguage() {
    applyLanguage(state.lang);
  }

  function applyLanguage(lang) {
    state.lang = lang;
    localStorage.setItem('nbpress_lang', lang);

    document.querySelectorAll('.lang-btn').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.lang === lang);
    });

    const dict = I18N[lang] || I18N.en;
    document.querySelectorAll('[data-i18n]').forEach(node => {
      const key = node.dataset.i18n;
      if (dict[key]) {
        node.textContent = dict[key];
      }
    });

    updateThemeButtonText();
  }

  // --- PWA Installation ---
  function initPWA() {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('./sw.js').catch(err => {
        console.warn('SW registration failed:', err);
      });
    }

    window.addEventListener('beforeinstallprompt', e => {
      e.preventDefault();
      deferredPrompt = e;
      if (el.installAppBtn) el.installAppBtn.classList.remove('hidden');
    });

    if (el.installAppBtn) {
      el.installAppBtn.addEventListener('click', () => {
        if (deferredPrompt) {
          deferredPrompt.prompt();
          deferredPrompt.userChoice.then(() => {
            deferredPrompt = null;
            el.installAppBtn.classList.add('hidden');
          });
        }
      });
    }
  }

  // --- Event Listeners ---
  function initEventListeners() {
    // Theme toggle cycle: system -> light -> dark -> system
    if (el.themeToggleBtn) {
      el.themeToggleBtn.addEventListener('click', () => {
        if (state.themeMode === 'auto') applyTheme('light');
        else if (state.themeMode === 'light') applyTheme('dark');
        else applyTheme('auto');
      });
    }

    // Language buttons
    document.querySelectorAll('.lang-btn').forEach(btn => {
      btn.addEventListener('click', () => applyLanguage(btn.dataset.lang));
    });

    // Dropzone & File Input
    if (el.dropzone && el.fileInput) {
      el.dropzone.addEventListener('click', () => el.fileInput.click());

      el.dropzone.addEventListener('dragover', e => {
        e.preventDefault();
        el.dropzone.classList.add('dragover');
      });

      el.dropzone.addEventListener('dragleave', () => {
        el.dropzone.classList.remove('dragover');
      });

      el.dropzone.addEventListener('drop', e => {
        e.preventDefault();
        el.dropzone.classList.remove('dragover');
        if (e.dataTransfer.files && e.dataTransfer.files.length) {
          handleFiles(e.dataTransfer.files);
        }
      });

      el.fileInput.addEventListener('change', e => {
        if (e.target.files && e.target.files.length) {
          handleFiles(e.target.files);
        }
      });
    }

    // Replace / Add files
    if (el.replaceFileBtn && el.fileInput) {
      el.replaceFileBtn.addEventListener('click', () => el.fileInput.click());
    }
    if (el.addFilesHeaderBtn && el.fileInput) {
      el.addFilesHeaderBtn.addEventListener('click', () => el.fileInput.click());
    }

    // Sample buttons
    document.querySelectorAll('.sample-btn').forEach(btn => {
      btn.addEventListener('click', e => {
        e.stopPropagation();
        const sampleType = btn.dataset.sample;
        loadSample(sampleType);
      });
    });

    // Layout selector cards
    document.querySelectorAll('.layout-card').forEach(card => {
      card.addEventListener('click', () => {
        document.querySelectorAll('.layout-card').forEach(c => c.classList.remove('active'));
        card.classList.add('active');
        state.config.layout = card.dataset.layout;
        updateLayoutDependentUI();
        recompile();
      });
    });

    // Theme selector pills (editorial, mcm, minimal)
    document.querySelectorAll('.theme-pill-btn').forEach(pill => {
      pill.addEventListener('click', () => {
        document.querySelectorAll('.theme-pill-btn').forEach(p => p.classList.remove('active'));
        pill.classList.add('active');
        state.config.theme = pill.dataset.theme;
        recompile();
      });
    });

    // Paper size buttons
    document.querySelectorAll('.seg-btn[data-paper]').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.seg-btn[data-paper]').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        state.config.paper = btn.dataset.paper;
        recompile();
      });
    });

    // Binding Gutter select
    const gutterSelect = document.getElementById('gutterSelect');
    if (gutterSelect) {
      gutterSelect.addEventListener('change', e => {
        state.config.gutter = e.target.value;
        recompile();
      });
    }

    // Duplex switch
    const duplexSwitch = document.getElementById('duplexSwitch');
    if (duplexSwitch) {
      duplexSwitch.addEventListener('change', e => {
        state.config.duplex = e.target.checked;
        recompile();
      });
    }

    // Hole punch switch
    const holeGuidesSwitch = document.getElementById('holeGuidesSwitch');
    if (holeGuidesSwitch) {
      holeGuidesSwitch.addEventListener('change', e => {
        state.config.holeGuides = e.target.checked;
        recompile();
      });
    }

    // Handout Note Style cards
    document.querySelectorAll('.note-style-card').forEach(card => {
      card.addEventListener('click', () => {
        document.querySelectorAll('.note-style-card').forEach(c => c.classList.remove('active'));
        card.classList.add('active');
        state.config.handoutNoteStyle = card.dataset.style;
        recompile();
      });
    });

    // Handout 1-up / 2-up toggle
    document.querySelectorAll('.seg-btn[data-handout-layout]').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.seg-btn[data-handout-layout]').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        state.config.handoutLayout = btn.dataset.handoutLayout;
        recompile();
      });
    });

    // Eco switch
    const ecoSwitch = document.getElementById('ecoSwitch');
    if (ecoSwitch) {
      ecoSwitch.addEventListener('change', e => {
        state.config.eco = e.target.checked;
        recompile();
      });
    }

    // Show Code & Prompts switches
    const showCodeSwitch = document.getElementById('showCodeSwitch');
    if (showCodeSwitch) {
      showCodeSwitch.addEventListener('change', e => {
        state.config.showCode = e.target.checked;
        recompile();
      });
    }

    // Zoom and Navigation controls
    if (el.prevPageBtn) el.prevPageBtn.addEventListener('click', () => previewController && previewController.prev());
    if (el.nextPageBtn) el.nextPageBtn.addEventListener('click', () => previewController && previewController.next());
    if (el.zoomInBtn) el.zoomInBtn.addEventListener('click', () => previewController && previewController.zoomIn());
    if (el.zoomOutBtn) el.zoomOutBtn.addEventListener('click', () => previewController && previewController.zoomOut());
    if (el.resetZoomBtn) el.resetZoomBtn.addEventListener('click', () => previewController && previewController.resetZoom());

    // Tabs switching
    if (el.tabPreviewBtn) el.tabPreviewBtn.addEventListener('click', () => switchTab('preview'));
    if (el.tabOutlineBtn) el.tabOutlineBtn.addEventListener('click', () => switchTab('outline'));
    if (el.tabTypstBtn) el.tabTypstBtn.addEventListener('click', () => switchTab('typst'));

    // Copy CLI Button
    if (el.copyCliBtn) {
      el.copyCliBtn.addEventListener('click', copyCliCommand);
    }

    // Direct Browser Print Button
    if (el.printPdfBtn) {
      el.printPdfBtn.addEventListener('click', () => {
        window.print();
      });
    }

    // Download Typst File Button
    if (el.downloadTypstBtn) {
      el.downloadTypstBtn.addEventListener('click', downloadTypstSource);
    }

    // Export Batch Button
    if (el.exportBatchBtn) {
      el.exportBatchBtn.addEventListener('click', exportBatchZip);
    }
  }

  function updateLayoutDependentUI() {
    if (el.handoutSettingsCard) {
      if (state.config.layout === 'handout') {
        el.handoutSettingsCard.classList.remove('hidden');
      } else {
        el.handoutSettingsCard.classList.add('hidden');
      }
    }
  }

  function switchTab(tab) {
    state.activeTab = tab;

    [el.tabPreviewBtn, el.tabOutlineBtn, el.tabTypstBtn].forEach(b => b && b.classList.remove('active'));
    [el.previewViewport, el.outlineViewContainer, el.typstViewContainer].forEach(c => c && c.classList.add('hidden'));

    if (tab === 'preview') {
      if (el.tabPreviewBtn) el.tabPreviewBtn.classList.add('active');
      if (el.previewViewport) el.previewViewport.classList.remove('hidden');
    } else if (tab === 'outline') {
      if (el.tabOutlineBtn) el.tabOutlineBtn.classList.add('active');
      if (el.outlineViewContainer) el.outlineViewContainer.classList.remove('hidden');
      renderOutlineView();
    } else if (tab === 'typst') {
      if (el.tabTypstBtn) el.tabTypstBtn.classList.add('active');
      if (el.typstViewContainer) el.typstViewContainer.classList.remove('hidden');
      renderTypstView();
    }
  }

  // --- File Processing ---
  function handleFiles(files) {
    const validFiles = Array.from(files).filter(f => f.name.endsWith('.ipynb'));
    if (!validFiles.length) {
      alert('Por favor selecciona archivos con extensión .ipynb (Jupyter Notebooks).');
      return;
    }

    let loadedCount = 0;
    validFiles.forEach(file => {
      const reader = new FileReader();
      reader.onload = function (e) {
        try {
          const parsed = window.NbpressEngine.parseNotebook(e.target.result, file.name);
          state.batchQueue.push(parsed);
          loadedCount++;
          if (loadedCount === validFiles.length) {
            setActiveNotebook(state.batchQueue[state.batchQueue.length - 1]);
            updateBatchBar();
          }
        } catch (err) {
          console.error('Error parsing notebook:', err);
          alert(`Error al procesar ${file.name}: archivo no es JSON válido.`);
        }
      };
      reader.readAsText(file);
    });
  }

  function loadSample(sampleType) {
    const url = sampleType === 'slides' ? './samples/slides.ipynb' : './samples/analysis.ipynb';
    const fallbackName = sampleType === 'slides' ? 'slides_example.ipynb' : 'quantitative_analysis.ipynb';

    fetch(url)
      .then(res => res.text())
      .then(jsonText => {
        const parsed = window.NbpressEngine.parseNotebook(jsonText, fallbackName);
        state.batchQueue = [parsed];
        if (sampleType === 'slides') {
          state.config.layout = 'slides';
          document.querySelectorAll('.layout-card').forEach(c => {
            c.classList.toggle('active', c.dataset.layout === 'slides');
          });
          updateLayoutDependentUI();
        }
        setActiveNotebook(parsed);
        updateBatchBar();
      })
      .catch(err => {
        console.error('Failed to load sample:', err);
        alert('No se pudo cargar el cuaderno de ejemplo.');
      });
  }

  function setActiveNotebook(nb) {
    state.activeNotebook = nb;
    el.initialHero.classList.add('hidden');
    el.workspace.classList.remove('hidden');

    // Update File Metadata bar
    if (el.metaFileName) el.metaFileName.textContent = nb.fileName;
    if (el.metaCellCount) el.metaCellCount.textContent = `${nb.stats.totalCells} celdas`;
    if (el.metaCodeCount) el.metaCodeCount.textContent = `${nb.stats.codeCells} código`;
    if (el.metaImagesCount) el.metaImagesCount.textContent = `${nb.stats.imagesCount} gráficos`;
    if (el.metaTablesCount) el.metaTablesCount.textContent = `${nb.stats.tablesCount} tablas`;
    if (el.metaSlidesCount) el.metaSlidesCount.textContent = `${nb.stats.slidesCount} slides`;

    recompile();
  }

  function updateBatchBar() {
    if (state.batchQueue.length > 1) {
      if (el.batchBar) el.batchBar.style.display = 'flex';
      if (el.batchCountBadge) el.batchCountBadge.textContent = state.batchQueue.length;

      if (el.batchTabsTrack) {
        el.batchTabsTrack.innerHTML = '';
        state.batchQueue.forEach((nb, idx) => {
          const tab = document.createElement('button');
          tab.type = 'button';
          tab.className = `batch-tab ${nb === state.activeNotebook ? 'active' : ''}`;
          tab.textContent = nb.fileName;
          tab.addEventListener('click', () => {
            setActiveNotebook(nb);
            updateBatchBar();
          });
          el.batchTabsTrack.appendChild(tab);
        });
      }
    } else {
      if (el.batchBar) el.batchBar.style.display = 'none';
    }
  }

  // --- Recompile & Render Pipeline ---
  function recompile() {
    if (!state.activeNotebook) return;

    // 1. Generate Print Sheets
    const sheets = window.NbpressEngine.generateSheets(state.activeNotebook, state.config);
    if (previewController) {
      previewController.setSheets(sheets);
    }

    // 2. Update CLI command snippet
    const cliCmd = window.NbpressEngine.buildCliCommand(state.activeNotebook, state.config);
    if (el.cliSnippet) {
      el.cliSnippet.textContent = cliCmd;
    }

    // 3. Update tabs if active
    if (state.activeTab === 'outline') renderOutlineView();
    if (state.activeTab === 'typst') renderTypstView();
  }

  function renderOutlineView() {
    if (!el.outlineViewContainer || !state.activeNotebook) return;
    const cells = state.activeNotebook.cells;

    let html = '<div class="cell-outline-list">';
    cells.forEach((c, idx) => {
      const typeClass = `cell-type-${c.type}`;
      const previewText = (c.source.trim().split('\n')[0] || '(celda vacía)').replace(/</g, '&lt;').replace(/>/g, '&gt;');
      html += `
        <div class="cell-outline-item">
          <div class="cell-outline-header">
            <span class="cell-type-badge ${typeClass}">Cell ${idx + 1} · ${c.type}</span>
            ${c.isSlideStarter ? `<span class="pill pill-accent">Slide: ${c.slideTitle}</span>` : ''}
          </div>
          <div class="cell-preview-text">${previewText}</div>
        </div>
      `;
    });
    html += '</div>';
    el.outlineViewContainer.innerHTML = html;
  }

  function renderTypstView() {
    if (!el.typstSourceCode || !state.activeNotebook) return;
    const typst = window.NbpressEngine.generateTypst(state.activeNotebook, state.config);
    el.typstSourceCode.textContent = typst;
  }

  // --- Export Actions ---
  function copyCliCommand() {
    if (!el.cliSnippet) return;
    const cmd = el.cliSnippet.textContent;
    navigator.clipboard.writeText(cmd).then(() => {
      const origText = el.copyCliBtn.textContent;
      el.copyCliBtn.textContent = '✓ Copiado';
      setTimeout(() => {
        el.copyCliBtn.textContent = origText;
      }, 1500);
    }).catch(err => {
      console.warn('Clipboard write failed:', err);
    });
  }

  function downloadTypstSource() {
    if (!state.activeNotebook) return;
    const typst = window.NbpressEngine.generateTypst(state.activeNotebook, state.config);
    const blob = new Blob([typst], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = state.activeNotebook.fileName.replace(/\.ipynb$/i, '.typ');
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  function exportBatchZip() {
    if (!state.batchQueue.length || typeof window.JSZip === 'undefined') return;

    const zip = new window.JSZip();
    state.batchQueue.forEach(nb => {
      const typst = window.NbpressEngine.generateTypst(nb, state.config);
      const name = nb.fileName.replace(/\.ipynb$/i, '.typ');
      zip.file(name, typst);
    });

    zip.generateAsync({ type: 'blob' }).then(content => {
      const url = URL.createObjectURL(content);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'nbpress_batch_export.zip';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    });
  }

  // Run on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
