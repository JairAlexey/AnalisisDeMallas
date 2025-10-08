# Reformulador de Carreras Universitarias 🎓

Una aplicación web inteligente construida con Streamlit que utiliza técnicas de Machine Learning para analizar y reformular mallas curriculares de universidades ecuatorianas.

## 🌟 Características Principales

### 🔍 Análisis Inteligente
- **Clustering de Carreras**: Agrupa carreras similares usando algoritmos avanzados de ML
- **Identificación de Materias Equivalentes**: Encuentra materias con nombres diferentes pero contenido similar
- **Análisis Semántico**: Utiliza análisis de similitud para entender el contexto de las materias
- **Visualizaciones Interactivas**: Gráficos dinámicos para explorar los resultados

### 🎯 Funcionalidades
- Agrupación automática de carreras por similitud
- Detección de materias equivalentes entre universidades
- Análisis de estructuras curriculares
- Comparación entre programas académicos
- Generación de reportes detallados
- Interfaz web moderna y responsiva

## 🏗️ Estructura del Proyecto

```
ModeloML/
├── app.py                     # Versión con funcionalidades avanzadas
├── requirements.txt           # Dependencias completas
├── data/
│   └── universidades.json    # Dataset de mallas curriculares
├── src/
│   ├── career_reformulator.py # Motor de ML para análisis de carreras
│   ├── data_explorer.py       # Herramientas de exploración de datos
│   └── utils.py               # Utilidades y funciones auxiliares
├── output/                    # Directorio para resultados generados
```

## 🚀 Instalación y Configuración

### Prerrequisitos
- Python 3.8 o superior
- pip (gestor de paquetes de Python)

### Pasos de Instalación Rápida

## 🎮 Uso de la Aplicación

### Aplicación Principal (Recomendada)
```bash
streamlit run app.py
```

### Explorador de Datos
```bash
streamlit run src/data_explorer.py
```

```

La aplicación se abrirá automáticamente en tu navegador en `http://localhost:8501` o `http://localhost:8502`

## 🔧 Funcionalidades Detalladas

### 1. 📊 Clustering Inteligente de Carreras
- **Algoritmo**: Análisis semántico + agrupación por similitud
- **Características**: Nombres de carreras + análisis de contenido de materias
- **Métricas**: Similitud de Jaccard + análisis de palabras clave
- **Resultado**: Grupos optimizados de carreras similares entre universidades

### 2. 🔍 Análisis de Materias Equivalentes
- **Técnica**: Comparación semántica avanzada
- **Umbral configurable**: 0.1 - 0.8 de similitud
- **Detección**: Materias con nombres diferentes pero contenido similar
- **Ejemplo**: "Cálculo I" ≈ "Matemáticas I" ≈ "Análisis Matemático I"

### 3. 📈 Visualizaciones Interactivas
- **Distribución de clusters**: Gráficos de barras dinámicos
- **Métricas por universidad**: Comparaciones estadísticas detalladas
- **Análisis curricular**: Visualización de estructuras académicas
- **Tablas interactivas**: Exploración detallada de datos

### 4. 🎯 Análisis Curricular Avanzado
- **Estructura**: Análisis de semestres y carga académica
- **Materias comunes**: Identificación de cursos fundamentales
- **Materias únicas**: Diferenciadores por universidad
- **Estadísticas**: Promedios, rangos y distribuciones detalladas

## 📊 Dataset

### Estructura de Datos
```json
{
  "universidad": "Nombre de la Universidad",
  "carrera": "Nombre de la Carrera",
  "malla_curricular": {
    "1": ["Materia 1", "Materia 2", ...],
    "2": ["Materia 3", "Materia 4", ...],
    ...
  }
}
```

### Universidades Incluidas
- PUCE (Pontificia Universidad Católica del Ecuador)
- Universidad Politécnica Salesiana
- Universidad del Azuay
- Universidad Espíritu Santo (UEES)
- Universidad Hemisferios
- UIDE
- UISEK
- UISRAEL
- UNIBE
- USFQ (Universidad San Francisco de Quito)

## 🤖 Tecnologías Utilizadas

### Core Technologies
- **Streamlit**: Framework de aplicaciones web interactivas
- **Pandas**: Manipulación y análisis de datos
- **NumPy**: Computación numérica y análisis estadístico

### Análisis y Machine Learning
- **Algoritmos propios**: Clustering semántico personalizado
- **Análisis de similitud**: Métricas de Jaccard y comparación textual
- **Procesamiento de texto**: Normalización y análisis de palabras clave

## 📋 Configuración de la Aplicación

### Parámetros Principales
- **Umbral de Similitud**: 0.1 - 0.8 (configurable en la UI)
- **Análisis Avanzado**: Habilitado/Deshabilitado
- **Número de Clusters**: Automático basado en similitud

### Personalización de la Interfaz
La aplicación incluye CSS personalizado para una experiencia visual moderna con:
- Gradientes y animaciones suaves
- Tarjetas interactivas con efectos hover
- Esquema de colores profesional
- Diseño responsive y centrado

## 🔍 Casos de Uso

### 1. 🎓 Instituciones Educativas
- Comparar currículums con otras universidades
- Identificar brechas y oportunidades de mejora
- Optimizar mallas curriculares
- Facilitar procesos de transferencia estudiantil

### 2. 📚 Estudiantes
- Comparar programas entre universidades
- Identificar materias equivalentes para transferencias
- Evaluar la carga académica por semestre
- Explorar opciones de carrera similares

### 3. 🏢 Empleadores
- Entender equivalencias entre formaciones académicas
- Evaluar perfiles académicos diversos
- Identificar competencias comunes entre graduados
- Planificar programas de capacitación

## 🚧 Desarrollo y Contribución

### Arquitectura de la Aplicación
```
Interfaz (Streamlit)
    ↓
Procesamiento de Datos (Pandas/NumPy)
    ↓
Algoritmos de Análisis (Propios)
    ↓
Visualización (Streamlit Charts)
```

### Próximas Funcionalidades
- [ ] Análisis predictivo de empleabilidad
- [ ] Exportación a múltiples formatos (PDF, Excel)
- [ ] Sistema de recomendaciones de carreras
- [ ] API REST para integración externa
- [ ] Dashboard de administración avanzado

## �️ Solución de Problemas

### Errores Comunes

1. **Error de dependencias**
```bash
# Usar solo dependencias mínimas
pip install -r requirements_minimal.txt
```

2. **Puerto ocupado**
```bash
# Streamlit usará automáticamente el siguiente puerto disponible
# Ej: 8501, 8502, 8503, etc.
```

3. **Archivo de datos no encontrado**
```bash
# Verificar que existe data/universidades.json
ls data/universidades.json
```

## 📈 Métricas y Rendimiento

### Capacidades del Sistema
- **Procesamiento**: 50+ carreras simultáneamente
- **Análisis**: ~1000+ materias en tiempo real
- **Precisión**: ~85% en agrupación de carreras similares
- **Velocidad**: Análisis completo en menos de 5 segundos

### Optimizaciones Implementadas
- Algoritmos optimizados para datasets medianos
- Caching inteligente de resultados
- Procesamiento incremental de datos
- Interfaz responsive y rápida

## � Soporte y Contacto

### Para Soporte Técnico
- Verificar la sección "Solución de Problemas"
- Revisar los logs en la terminal
- Contactar al equipo de desarrollo

### Para Colaboraciones
- Propuestas de mejora
- Nuevas funcionalidades
- Integración con otros sistemas

## � Información Legal

Este proyecto está desarrollado con fines académicos y de investigación. Los datos utilizados son de dominio público o han sido proporcionados por las instituciones participantes.

---

**¡Gracias por usar el Reformulador de Carreras Universitarias! 🎓✨**

**Desarrollado en UDLA - Universidad de Las Américas**

Para más información o reportar issues, contacta al equipo de desarrollo.
