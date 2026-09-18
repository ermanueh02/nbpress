"""
Script to create sample Jupyter notebooks for testing nbpress.
"""

import base64
import io
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import nbformat as nbf
import numpy as np
import pandas as pd


def create_samples():
    samples_dir = Path(__file__).parent / "sample_notebooks"
    samples_dir.mkdir(parents=True, exist_ok=True)

    # 1. Generate plot image base64
    fig, ax = plt.subplots(figsize=(6, 3), dpi=150)
    x = np.linspace(0, 10, 200)
    ax.plot(x, np.sin(x), label="Seno: sin(x)", color="#0d6efd", lw=2)
    ax.plot(x, np.cos(x), label="Coseno: cos(x)", color="#dc3545", lw=2, linestyle="--")
    ax.set_title("Oscilaciones Armonicas Simples")
    ax.set_xlabel("Tiempo t (segundos)")
    ax.set_ylabel("Amplitud A")
    ax.grid(True, alpha=0.3)
    ax.legend()
    plt.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    plt.close(fig)
    buf.seek(0)
    img_b64 = base64.b64encode(buf.read()).decode("utf-8")

    # 2. Complete Features Notebook
    nb1 = nbf.v4.new_notebook()
    nb1.metadata = {
        "title": "Analisis Cuantitativo y Modelado Estadistico",
        "authors": [{"name": "Dra. Elena Ruiz"}, {"name": "Prof. Carlos Mendoza"}],
    }

    # Cell 1: Header and abstract
    nb1.cells.append(
        nbf.v4.new_markdown_cell(
            """# Analisis Cuantitativo y Modelado Estadistico

> Este documento presenta un estudio exhaustivo sobre transformaciones matematicas, modelos de probabilidad y analisis de datos experimentales preparado para publicacion e impresion de alta calidad.

## 1. Fundamentos Teoricos y Modelos Matematicos

Consideramos una funcion de densidad de probabilidad gaussiana univariada dada por:

$$f(x) = \\frac{1}{\\sigma \\sqrt{2\\pi}} \\exp\\left( -\\frac{(x - \\mu)^2}{2\\sigma^2} \\right)$$

Donde $\\mu$ representa la media y $\\sigma^2$ la varianza. Ademas, para la matriz de covarianza $\\mathbf{\\Sigma}$ en dimension $2 \\times 2$:

$$\\mathbf{\\Sigma} = \\begin{pmatrix} \\sigma_{11} & \\sigma_{12} \\\\ \\sigma_{21} & \\sigma_{22} \\end{pmatrix}$$

### Tabla de Parametros Estimados

| Parametro | Valor Estimado | Error Estandar | Intervalo 95% |
| :--- | :---: | :---: | :---: |
| $\\alpha$ (Interseccion) | 2.451 | 0.082 | [2.29, 2.61] |
| $\\beta_1$ (Pendiente) | 0.892 | 0.034 | [0.82, 0.96] |
| $R^2$ (Ajuste) | 0.941 | - | - |
"""
        )
    )

    # Cell 2: Code cell generating plot
    nb1.cells.append(
        nbf.v4.new_code_cell(
            source="""# Generacion del grafico de oscilaciones
import numpy as np
import matplotlib.pyplot as plt

x = np.linspace(0, 10, 200)
plt.plot(x, np.sin(x), label='sin(x)')
plt.plot(x, np.cos(x), label='cos(x)', linestyle='--')
plt.title('Oscilaciones Armonicas')
plt.show()""",
            execution_count=1,
            outputs=[
                nbf.v4.new_output(
                    output_type="display_data",
                    data={"image/png": img_b64},
                )
            ],
        )
    )

    # Cell 3: Markdown and DataFrame
    df = pd.DataFrame(
        {
            "Variable": ["X1", "X2", "X3", "X4"],
            "Media": [10.5, 23.1, 45.8, 12.4],
            "Std": [1.2, 2.4, 5.1, 0.9],
            "P-valor": [0.001, 0.042, 0.0001, 0.12],
        }
    )
    df_html = df.to_html(index=False)

    nb1.cells.append(
        nbf.v4.new_markdown_cell(
            """## 2. Inspeccion del DataFrame de Variables Experimentales

A continuacion observamos las estadisticas resumidas calculadas mediante Pandas:"""
        )
    )

    nb1.cells.append(
        nbf.v4.new_code_cell(
            source="""df = pd.DataFrame({
    'Variable': ['X1', 'X2', 'X3', 'X4'],
    'Media': [10.5, 23.1, 45.8, 12.4],
    'Std': [1.2, 2.4, 5.1, 0.9],
    'P-valor': [0.001, 0.042, 0.0001, 0.12]
})
df""",
            execution_count=2,
            outputs=[
                nbf.v4.new_output(
                    output_type="execute_result",
                    data={"text/html": df_html, "text/plain": df.to_string()},
                    execution_count=2,
                )
            ],
        )
    )

    # Cell 4: Code with stdout stream
    nb1.cells.append(
        nbf.v4.new_code_cell(
            source="""print('Procesando muestras...')
for i in range(5):
    print(f'Muestra #{i+1}: OK (Score: {0.95 + i*0.01:.3f})')
print('Simulacion completada con exito.')""",
            execution_count=3,
            outputs=[
                nbf.v4.new_output(
                    output_type="stream",
                    name="stdout",
                    text="""Procesando muestras...
Muestra #1: OK (Score: 0.950)
Muestra #2: OK (Score: 0.960)
Muestra #3: OK (Score: 0.970)
Muestra #4: OK (Score: 0.980)
Muestra #5: OK (Score: 0.990)
Simulacion completada con exito.
""",
                )
            ],
        )
    )

    with open(samples_dir / "complete_features.ipynb", "w", encoding="utf-8") as f:
        nbf.write(nb1, f)

    # 3. Slides / Handout Notebook
    nb2 = nbf.v4.new_notebook()
    nb2.metadata = {
        "title": "Introduccion al Aprendizaje Automatico",
        "authors": [{"name": "Prof. Manuel Ramos"}],
    }

    s1 = nbf.v4.new_markdown_cell(
        """# Diapositiva 1: Conceptos Basicos de ML
El aprendizaje automatico se divide principalmente en:
- **Supervisado**: Regresion y Clasificacion con etiquetas conocidas.
- **No Supervisado**: Clustering y reduccion de dimensionalidad.
- **Por Refuerzo**: Aprendizaje basado en recompensas y castigos."""
    )
    s1.metadata["slideshow"] = {"slide_type": "slide"}
    nb2.cells.append(s1)

    s2 = nbf.v4.new_markdown_cell(
        """# Diapositiva 2: Funcion de Perdida (MSE)
Para un modelo lineal, la perdida de error cuadratico medio es:

$$L(\\theta) = \\frac{1}{N} \\sum_{i=1}^{N} (y_i - \\hat{y}_i)^2$$

El objetivo es encontrar $\\theta^*$ que minimice $L(\\theta)$."""
    )
    s2.metadata["slideshow"] = {"slide_type": "slide"}
    nb2.cells.append(s2)

    s3 = nbf.v4.new_code_cell(
        source="""# Entrenamiento de un regresor Ridge
from sklearn.linear_model import Ridge
model = Ridge(alpha=1.0)
print('Modelo inicializado con regularizacion L2')""",
        execution_count=1,
        outputs=[
            nbf.v4.new_output(
                output_type="stream",
                name="stdout",
                text="Modelo inicializado con regularizacion L2\n",
            )
        ],
    )
    s3.metadata["slideshow"] = {"slide_type": "slide"}
    nb2.cells.append(s3)

    with open(samples_dir / "slides_example.ipynb", "w", encoding="utf-8") as f:
        nbf.write(nb2, f)

    print("Sample notebooks created successfully at:", samples_dir)


if __name__ == "__main__":
    create_samples()
